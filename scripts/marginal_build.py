"""M3 recent additions and M4 planned additions: average emission rate of recently built / planned capacity (PLAN_marginal §M3-M4).

Units are plant x prime-mover groups (combined-cycle CT/CA/CS parts merged), the finest level at which EIA-923 reports
both generation and fuel. Operating dates and BA from EIA-860M (Sep 2026); 2025 generation and fuel for electricity from
EIA-923 2025 Final (Page 1). Storage excluded. Gas CO2e via em.intensity() per MMBtu at L = 2.3% with prime-mover slip.

Inputs (gitignored, in data/marginal/tmp/): eia860m_sep2026.xlsx, EIA923_Schedules_2_3_4_5_M_12_2025_Final.xlsx.
Writes results/marginal/build_margins.csv and build_margin_samples.csv.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

import emissions as em
from cases import CMM, F_SUPPLY, GRID_LOSS, L_PRIMARY

ROOT = Path(__file__).resolve().parents[1]
TMP = ROOT / 'data' / 'marginal' / 'tmp'
OUT = ROOT / 'results' / 'marginal'
OUT.mkdir(parents=True, exist_ok=True)
GWP = em.GWP['AR6_100']
REGIONS = {'ERCOT': ['ERCO'], 'PJM': ['PJM'], 'US': None}
SLIP = {'IC': 0.522, 'GT': 0.004, 'CC': 0.004}     # kg CH4/MMBtu (40 CFR 98 Table W-7), as for the off-grid cases
COAL = {'BIT': 93.28, 'SUB': 97.17, 'LIG': 97.72, 'RC': 93.28, 'WC': 93.28, 'SGC': 93.28}   # kg CO2/MMBtu, Table C-1
OIL = {'DFO': 73.96, 'RFO': 75.10, 'KER': 75.20, 'JF': 72.22, 'WO': 74.0, 'PC': 102.41}
CC_PARTS = {'CT', 'CA', 'CS'}
STORAGE = {'BA', 'PS', 'FW', 'CE', 'ES'}
CONSTRUCTION = {'(U)', '(V)', '(TS)'}


def pm_group(pm):
    return 'CC' if pm in CC_PARTS else pm


def tech_class(row):
    t, pm = row['Technology'], row['pmg']
    if pm in STORAGE or t == 'Batteries':
        return 'storage'
    if 'Solar' in t:
        return 'solar'
    if 'Wind' in t:
        return 'wind_off' if 'Offshore' in t else 'wind'
    if 'Natural Gas' in t or t == 'Other Natural Gas':
        return {'CC': 'gas_cc', 'GT': 'gas_ct', 'IC': 'gas_ic'}.get(pm, 'gas_other')
    return {'Nuclear': 'nuclear', 'Conventional Hydroelectric': 'hydro', 'Geothermal': 'geothermal',
            'Conventional Steam Coal': 'coal'}.get(t, 'other')


def read_860m(sheet):
    d = pd.read_excel(TMP / 'eia860m_sep2026.xlsx', sheet_name=sheet, header=2)
    d = d[pd.to_numeric(d['Plant ID'], errors='coerce').notna()].copy()
    d['Plant ID'] = d['Plant ID'].astype(int)
    d['pmg'] = d['Prime Mover Code'].map(pm_group)
    d['tech'] = d.apply(tech_class, axis=1)
    return d


def read_923():
    p = TMP / 'eia923_2025_page1.parquet'
    if not p.exists():
        d = pd.read_excel(TMP / 'EIA923_Schedules_2_3_4_5_M_12_2025_Final.xlsx', sheet_name='Page 1 Generation and Fuel Data', header=5)
        d.columns = [c.replace('\n', ' ') for c in d.columns]
        d = d[['Plant Id', 'Plant State', 'Reported Prime Mover', 'Reported Fuel Type Code', 'Balancing Authority Code',
               'Elec Fuel Consumption MMBtu', 'Net Generation (Megawatthours)']]
        d.columns = ['plant', 'state', 'pm', 'fuel', 'ba', 'mmbtu', 'mwh']
        d = d[pd.to_numeric(d['plant'], errors='coerce').notna() & (d.plant != 99999)]
        d['plant'] = d['plant'].astype(int)
        d.to_parquet(p, index=False)
    d = pd.read_parquet(p)
    d['pmg'] = d['pm'].map(pm_group)
    return d


def co2e_per_mmbtu(fuel, pmg):
    if fuel == 'NG':
        return em.intensity(1.0, SLIP.get(pmg, 0.001), L_PRIMARY, supply_co2_frac=F_SUPPLY)
    if fuel in COAL:
        return COAL[fuel] + CMM * GWP['ch4']
    if fuel in OIL:
        return OIL[fuel]
    return 0.0   # biomass, waste heat, other: zero here (rare in recent builds; reported in the sample file)


def group_table(op, g923):
    """One row per plant x prime-mover group with operating dates, capacity, 2025 MWh and CO2e."""
    op = op.copy()
    op['date'] = pd.to_datetime(dict(year=op['Operating Year'].astype(int), month=op['Operating Month'].astype(int), day=1))
    grp = op.groupby(['Plant ID', 'pmg']).agg(ba=('Balancing Authority Code', 'first'), state=('Plant State', 'first'),
                                              name=('Plant Name', 'first'), tech=('tech', lambda s: s.mode().iloc[0]),
                                              mw=('Nameplate Capacity (MW)', 'sum'), date_max=('date', 'max'),
                                              date_min=('date', 'min')).reset_index()
    g923 = g923.copy()
    g923['co2e'] = [m * co2e_per_mmbtu(f, p) for m, f, p in zip(g923.mmbtu, g923.fuel, g923.pmg)]
    g923['gas_mmbtu'] = np.where(g923.fuel == 'NG', g923.mmbtu, 0.0)
    gen = g923.groupby(['plant', 'pmg'])[['mwh', 'mmbtu', 'gas_mmbtu', 'co2e']].sum().reset_index()
    grp = grp.merge(gen, left_on=['Plant ID', 'pmg'], right_on=['plant', 'pmg'], how='left').drop(columns='plant')
    grp['mixed_vintage'] = (grp.date_max - grp.date_min).dt.days > 3 * 365
    return grp


def tool07_sample(grp, total_mwh):
    """Most recent groups summing to >= 20% of regional generation, or the 5 most recent if larger (Tool 07 rule as
    quoted in the Verra Oct 2024 draft). Groups need a full year of 2025 data (all units online by Dec 2024)."""
    g = grp[(grp.tech != 'storage') & (grp.date_max < '2025-01-01') & ~grp.mixed_vintage & (grp.mwh > 0)]
    g = g.sort_values('date_max', ascending=False)
    cum = g.mwh.cumsum()
    s20 = g[cum.shift(fill_value=0) < 0.2 * total_mwh]
    s5 = g.head(5)
    return s20 if s20.mwh.sum() >= s5.mwh.sum() else s5


def rate(sample):
    return float(sample.co2e.sum() / sample.mwh.sum() / (1 - GRID_LOSS))


def main():
    op, pl, g923 = read_860m('Operating'), read_860m('Planned'), read_923()
    grp = group_table(op, g923)
    rows, samples = [], []
    lower48 = ~grp.state.isin(['AK', 'HI'])
    for reg, bas in REGIONS.items():
        in_reg = grp.ba.isin(bas) if bas else lower48
        g = grp[in_reg]
        reg923 = g923[g923.ba.isin(bas)] if bas else g923[~g923.state.isin(['AK', 'HI'])]
        total = float(reg923[~reg923.pm.isin(STORAGE)].mwh.sum())
        # M3 primary: Tool 07 sample
        s = tool07_sample(g, total)
        rows.append(dict(region=reg, metric='recent additions (Tool 07 20% sample)', value=rate(s), n_groups=len(s),
                         twh=s.mwh.sum() / 1e6, share_of_gen=s.mwh.sum() / total, oldest=str(s.date_max.min().date()),
                         gas_share_mwh=s[s.tech.str.startswith('gas')].mwh.sum() / s.mwh.sum(),
                         excluded_mixed_vintage=int(g.mixed_vintage.sum())))
        samples.append(s.assign(region=reg, sample='tool07'))
        # M3 variant: fixed window 2020-2024
        w = g[(g.date_min >= '2020-01-01') & (g.date_max < '2025-01-01') & (g.tech != 'storage') & (g.mwh > 0)]
        rows.append(dict(region=reg, metric='recent additions (online 2020-2024)', value=rate(w), n_groups=len(w),
                         twh=w.mwh.sum() / 1e6, share_of_gen=w.mwh.sum() / total,
                         gas_share_mwh=w[w.tech.str.startswith('gas')].mwh.sum() / w.mwh.sum()))
        samples.append(w.assign(region=reg, sample='2020-2024'))
        # capacity factors and gas heat rates from units online 2020-2024 (region; national fallback)
        nat = grp[lower48 & (grp.date_min >= '2020-01-01') & (grp.date_max < '2025-01-01') & (grp.mwh > 0)]

        def cf_hr(tech):
            for src in (w, nat):
                t = src[src.tech == tech]
                if t.mw.sum() > 50:
                    return t.mwh.sum() / (t.mw.sum() * 8760), (t.co2e.sum() / t.mwh.sum())
            return np.nan, np.nan
        par = {t: cf_hr(t) for t in ['solar', 'wind', 'wind_off', 'gas_cc', 'gas_ct', 'gas_ic', 'gas_other', 'geothermal', 'hydro', 'other']}
        par['nuclear'] = (0.92, 0.0)   # no recent new-build nuclear fleet to measure; ~US fleet average CF, zero direct emissions
        par['wind_off'] = par['wind_off'] if not np.isnan(par['wind_off'][0]) else (0.40, 0.0)
        # M4: planned 2026-2030
        p = pl[(pl['Planned Operation Year'].between(2026, 2030)) & (pl.tech != 'storage')]
        p = p[p['Balancing Authority Code'].isin(bas)] if bas else p[~p['Plant State'].isin(['AK', 'HI'])]
        for label, st in (('planned additions 2026-2030 (under construction)', CONSTRUCTION), ('planned additions 2026-2030 (all statuses)', None)):
            q = p[p.Status.str[:4].str.strip().isin(st)] if st else p
            q = q.assign(cf=q.tech.map(lambda t: par.get(t, (np.nan, np.nan))[0]),
                         ci=q.tech.map(lambda t: par.get(t, (np.nan, np.nan))[1]))
            q = q.assign(mwh=q['Nameplate Capacity (MW)'] * 8760 * q.cf)
            q = q.assign(co2e=q.mwh * q.ci)
            ok = q.mwh.notna()
            rows.append(dict(region=reg, metric=label, value=float(q[ok].co2e.sum() / q[ok].mwh.sum()) / (1 - GRID_LOSS),
                             n_groups=len(q), twh=q[ok].mwh.sum() / 1e6, gw=q['Nameplate Capacity (MW)'].sum() / 1e3,
                             gas_share_mwh=q[ok & q.tech.str.startswith('gas')].mwh.sum() / q[ok].mwh.sum(),
                             unparameterized_gw=q[~ok]['Nameplate Capacity (MW)'].sum() / 1e3,
                             mix_gw=json.dumps(q.groupby('tech')['Nameplate Capacity (MW)'].sum().div(1e3).round(2).to_dict())))
        rows[-1]['params'] = json.dumps({k: [round(v[0], 3), round(v[1], 1)] for k, v in par.items()})
    df = pd.DataFrame(rows)
    df.to_csv(OUT / 'build_margins.csv', index=False)
    pd.concat(samples).to_csv(OUT / 'build_margin_samples.csv', index=False)
    with pd.option_context('display.width', 250, 'display.max_columns', 20):
        print(df.drop(columns=['params', 'mix_gw'], errors='ignore').round(3).to_string())
        print(df[['region', 'metric', 'mix_gw']].dropna().to_string())


if __name__ == '__main__':
    main()
