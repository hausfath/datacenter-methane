"""Lifetime levelized cost ($/MWh delivered) of off-grid gas power for a data center, vs grid supply.

Quick estimate, not pre-registered. Inputs and sources are listed in COSTS.md; heat rates are imported from cases.py so
the cost and emissions numbers use the same machines.

Basis: nominal dollars, levelized flat over the plant life (the Lazard convention, comparable to a flat PPA price).
Capital charge uses the fixed-charge-rate method: FCR = CRF(after-tax WACC, life) x (1 - T x PV(depreciation)) / (1 - T),
times an interest-during-construction factor. O&M escalates at 2.25%/yr (Lazard); fuel follows a nominal price path.
"""
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import binom

from cases import CASES, BTM_LOSS

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/costs'
OUT.mkdir(parents=True, exist_ok=True)

INFL = 0.025            # assumed GDP-deflator inflation, used only to move EIA 2022$/2023$ capex to 2026$
OM_ESC = 0.0225         # Lazard LCOE+ 2026 "O&M Escalation Rate 2.25%"
COD = 2027
LIFE = 20

# MACRS half-year tables (IRS Pub 946 Table A-1), fractions of basis
MACRS = {
    5: [.20, .32, .192, .1152, .1152, .0576],
    15: [.05, .095, .0855, .077, .0693, .0623, .059, .059, .0591, .059, .0591, .059, .0591, .059, .0591, .0295],
    20: [.0375, .07219, .06677, .06177, .05713, .05285, .04888, .04522, .04462, .04461, .04462, .04461, .04462,
         .04461, .04462, .04461, .04462, .04461, .04462, .04461, .02231],
    'bonus': [1.0],     # OBBBA 100% bonus depreciation (property acquired after 19 Jan 2025)
}

# Lazard LCOE+ 2026 financing: 60% debt at 8%, 40% equity at 12%, 40% combined tax -> after-tax WACC 7.7%
FIN_LAZARD = dict(wacc=0.6 * 0.08 * (1 - 0.40) + 0.4 * 0.12, tax=0.40)
# Central case: same capital structure, 25.7% combined tax (21% federal + ~6% state, net of federal deduction)
FIN_CENTRAL = dict(wacc=0.6 * 0.08 * (1 - 0.257) + 0.4 * 0.12, tax=0.257)

# ---------------------------------------------------------------- technologies (2026$ overnight capex, central / low / high)
# Current-order pricing. Brattle/S&L ERCOT CONE draft (Oct 2026): H-frame CT $1,853/kW (2026$), +51% nominal since the
# 2025 PJM CONE study; Brattle ERCOT CONE workshop (Feb 2026): small frames/aeroderivatives/RICE "recent estimates for
# these approach or exceed $3,000/kW overnight costs". EIA AEO2026 (Table 3, 2025$) is built on the 2025 PJM study and lags.
d22, d23, d25 = (1 + INFL) ** 4, (1 + INFL) ** 3, (1 + INFL)
POST_PJM = 1.51          # Brattle: frame CT overnight cost +51% nominal since the 2025 PJM CONE study (AEO2026's basis)
TECH = {
    'Recip engines (lean-burn)': dict(
        capex=(3000, 2240 * d22, 2275 * d25 * POST_PJM),  # central: Brattle ~$3,000; low: EIA AEO2023 ICE (pre-boom)
        fom=39.57 * d22, vom=6.40 * d22,             # EIA AEO2023 ICE (AEO2026 dropped the ICE row)
        unit_mw=4.4, avail=0.95, build_months=18, macrs=15),
    'Simple-cycle turbines': dict(
        capex=(3000, 2275 * d25, 2275 * d25 * POST_PJM),  # central: Brattle ~$3,000; low: AEO2026 aero; high: AEO2026 x 1.51
        fom=9.99 * d25, vom=5.97 * d25,             # EIA AEO2026 aeroderivative CT
        unit_mw=35.0, avail=0.95, build_months=30, macrs=15),
    'Fuel cells (Bloom SOFC)': dict(
        capex=(5700, 3000, 8287 * d25),             # central: AEP Cheyenne $4B / 702 MW; high: EIA AEO2026 fuel cell total overnight
        fom=37.77 * d25, vom=0.72 * d25,             # EIA AEO2026 fuel cell
        stack=0.15,                                 # stack replacement, share of capex in years 5, 10, 15 (assumption)
        unit_mw=0.3, avail=0.97, build_months=12, macrs=5),
    'Combined cycle (on site)': dict(
        capex=(2400, 2100, 2600),                   # Lazard 2026: range top $2,100; market quotes $2,400-2,600
        fom=20.0, vom=4.0,                          # inside Lazard 2026 CC ranges (FOM 10-25.5, VOM 2.75-5)
        unit_mw=250.0, avail=0.92, build_months=36, macrs=20),
}
BESS = dict(capex=1521 * d25, fom=41.84 * d25)      # EIA AEO2026 battery storage (150 MW), per kW


# ---------------------------------------------------------------- gas price paths ($/MMBtu, nominal)
def aeo_nominal(fname):
    import openpyxl
    rows = list(openpyxl.load_workbook(ROOT / 'data/costs' / fname, read_only=True, data_only=True).active.iter_rows(values_only=True))
    years = [y for y in rows[9][1:] if isinstance(y, int)]
    nom = next(r for r in rows if r[0] == 'NGS000:nom_HenryHub')
    return dict(zip(years, nom[2:2 + len(years)]))


AEO25, AEO26 = aeo_nominal('aeo2025_ref_table13.xlsx'), aeo_nominal('aeo2026_cb_table13.xlsx')
STRIP = {2027: 3.003, 2028: 3.635}                  # NYMEX calendar strips, settle 26 Oct 2026 (NRG daily update)
DELIVERED_ADDER = 0.33   # EIA STEO Oct 2026 power-sector gas cost minus Henry Hub, 2025-27 mean (3.87-3.53, 3.94-3.48, 3.34-3.16)
WAHA = {2027: -1.57, 2028: -2.03}                   # Aegis Waha basis: Summer '27, Winter '27/28 (Oct 2026)
WAHA_LONG = -0.50                                   # assumed post-pipeline basis from 2031 (no market quote)


def extend(path, last=2070):
    """AEO tables end in 2050; hold the 2045-50 nominal growth rate after that."""
    g = (path[2050] / path[2045]) ** (1 / 5)
    for y in range(2051, last + 1):
        path[y] = path[y - 1] * g
    return path


AEO25, AEO26 = extend(AEO25), extend(AEO26)


def gas_path(case='central'):
    yrs = range(COD, COD + 40)
    if case == 'aeo2026':
        return {y: AEO26[y] + DELIVERED_ADDER for y in yrs}
    if case == 'strip_flat':    # 2027-28 strip, then the 2028 strip rising with inflation only
        return {y: STRIP.get(y, STRIP[2028] * (1 + OM_ESC) ** (y - 2028)) + DELIVERED_ADDER for y in yrs}
    p = {}
    for y in yrs:
        if y in STRIP:
            hh = STRIP[y]
        elif y < 2032:      # linear blend from the 2028 strip to AEO2025 Reference by 2032
            w = (y - 2028) / (2032 - 2028)
            hh = (1 - w) * STRIP[2028] + w * AEO25[y]
        else:
            hh = AEO25[y]
        if case == 'waha':
            basis = WAHA.get(y, WAHA[2028] + (WAHA_LONG - WAHA[2028]) * min(1, (y - 2028) / 3))
            p[y] = max(hh + basis, 0.25) + 0.10     # short lateral only
        else:
            p[y] = hh + DELIVERED_ADDER
    return p


# ---------------------------------------------------------------- finance
def crf(r, n):
    return r * (1 + r) ** n / ((1 + r) ** n - 1)


def fcr(wacc, tax, life, macrs):
    sched = MACRS[macrs]
    pvd = sum(d / (1 + wacc) ** (t + 1) for t, d in enumerate(sched))
    return crf(wacc, life) * (1 - tax * pvd) / (1 - tax)


def idc(wacc, months):
    """Spend spread evenly over construction, carried at the WACC to COD."""
    yrs = months / 12
    return ((1 + wacc) ** yrs - 1) / (np.log(1 + wacc) * yrs) if yrs > 0 else 1.0


def level(series, wacc):
    """Flat nominal value with the same PV as a yearly series (years 1..n)."""
    t = np.arange(1, len(series) + 1)
    d = (1 + wacc) ** -t
    return float(np.sum(np.asarray(series) * d) / np.sum(d))


def lcoe(capex, fom, vom, hr, cf, fuel, life=LIFE, fin=FIN_CENTRAL, macrs=15, build_months=24, om_esc=OM_ESC,
         extra_capex_yrs=None, parts=False):
    """$/MWh generated. capex $/kW, fom $/kW-yr (year-1), vom $/MWh (year-1), hr MMBtu/MWh, fuel: list of $/MMBtu by year.

    extra_capex_yrs: {year_index: $/kW} for mid-life replacements (expensed through the capital charge as a PV lump).
    """
    w, T = fin['wacc'], fin['tax']
    mwh_per_kw = 8.76 * cf
    k = capex * idc(w, build_months)
    if extra_capex_yrs:
        k += sum(v / (1 + w) ** yr for yr, v in extra_capex_yrs.items())
    cap = k * fcr(w, T, life, macrs) / mwh_per_kw
    esc = (1 + om_esc) ** np.arange(life)
    out = dict(capital=cap, fixed_om=level(fom * esc, w) / mwh_per_kw, var_om=level(vom * esc, w),
               fuel=level(hr * np.asarray(fuel[:life]), w))
    return out if parts else sum(out.values())


# ---------------------------------------------------------------- 1. reproduce Lazard LCOE+ 2026 (v19.0) gas rows
def lazard_check():
    # page "Levelized Cost of Energy—Assumptions (cont'd)": capex, FOM, VOM, HR, CF, $3.45 fuel, 24-month build, 30-yr life
    rows = [('Gas peaking low', 1100, 10.0, 3.50, 10.275, 0.15, 144, 98),
            ('Gas peaking high', 1650, 17.0, 5.00, 11.175, 0.10, 276, 213),
            ('Gas CC low', 1450, 10.0, 2.75, 6.475, 0.90, 51, 25),
            ('Gas CC high', 2100, 25.5, 5.00, 6.550, 0.30, 129, 92)]
    out = []
    for macrs in (15, 20):
        for esc in (0.0, OM_ESC):
            for name, k, f, v, h, cf, pub, pub_cap in rows:
                p = lcoe(k, f, v, h, cf, [3.45] * 30, life=30, fin=FIN_LAZARD, macrs=macrs, build_months=24, om_esc=esc, parts=True)
                tot = sum(p.values())
                out.append(dict(macrs=macrs, om_esc=esc, row=name, published=pub, ours=tot, err_pct=100 * (tot / pub - 1),
                                published_capital=pub_cap, ours_capital=p['capital']))
    df = pd.DataFrame(out)
    df.to_csv(OUT / 'lazard_reproduction.csv', index=False, float_format='%.2f')
    return df


# ---------------------------------------------------------------- 2. redundancy: units needed to carry peak load
def units_needed(peak_mw, unit_mw, avail, target=0.9999):
    n = int(np.ceil(peak_mw / unit_mw))
    m = n
    while binom.sf(n - 1, m, avail) < target:    # P(available units >= n)
        m += 1
    return n, m


def case_lcoe(tech, site_mw=300, lf=0.80, capex_case=0, system=True, fin=FIN_CENTRAL, gas='central', life=LIFE,
              target=0.9999, avail=None, unit_mw=None, hr_mult=1.0, bess_frac=0.0, stack=None, itc=0.0, macrs=None,
              ptax=0.0, idc_mult=None, parts=False):
    """$/MWh delivered to the data center (after BTM_LOSS). Plant is sized to peak load; LF = average/peak load."""
    p = TECH[tech]
    hr = CASES[tech][0] * hr_mult
    um, av = unit_mw or p['unit_mw'], avail or p['avail']
    n, m = units_needed(site_mw, um, av, target) if system else (1, 1)
    over = m / n if system else 1.0
    cf = lf / over
    capex = p['capex'][capex_case] * (1 - itc)
    st = p.get('stack', 0.0) if stack is None else stack
    extra = {y: st * p['capex'][capex_case] for y in (5, 10, 15) if y < life} if st else None
    fuel = list(gas_path(gas).values())
    fom = p['fom'] + ptax * p['capex'][capex_case]   # property tax + insurance as a share of capex per year
    out = lcoe(capex * (idc_mult / idc(fin['wacc'], p['build_months']) if idc_mult else 1.0), fom, p['vom'], hr, cf, fuel,
               life=life, fin=fin, macrs=macrs or p['macrs'], build_months=p['build_months'], extra_capex_yrs=extra, parts=True)
    if bess_frac:
        b = lcoe(BESS['capex'], BESS['fom'], 0, 0, lf, [0] * life, life=life, fin=fin, macrs=5, build_months=12, parts=True)
        out['bess'] = bess_frac * (b['capital'] + b['fixed_om'])
    out = {k: v / (1 - BTM_LOSS) for k, v in out.items()}
    meta = dict(n_units=n, m_units=m, overbuild=over, plant_cf=cf)
    return (out, meta) if parts else sum(out.values())


# ---------------------------------------------------------------- 3. grid comparison ($/MWh, nominal, year-1 values)
def grid_refs():
    lf = 0.80
    # PJM 2026/27 BRA $329.17/MW-day. Assumes the site is at peak draw during PJM's coincident peaks (summer cooling),
    # so PLC = average/LF; with PLC = average load it would be 329.17*365/8760 = $13.7/MWh.
    cap_2627 = 329.17 * 365 / 8760 / lf
    refs = {
        'PJM wholesale + transmission, 2025 (IMM total price)': 82.67,
        'PJM same, capacity at 2026/27 BRA, 80% LF': 82.67 - 13.09 + cap_2627,   # IMM 2025 capacity was $13.09/MWh
        'ERCOT wholesale all-in, 2025 (IMM: 2024 $34 x 1.138)': 34 * 1.138,
        'EIA industrial retail, Jan-Aug 2026: US': 90.9,
        'EIA industrial retail, Jan-Aug 2026: Texas': 67.7,
        'EIA industrial retail, Jan-Aug 2026: Virginia': 100.7,
        'EIA industrial retail, Jan-Aug 2026: Ohio': 102.3,
        'EIA industrial retail, Jan-Aug 2026: Pennsylvania': 108.2,
    }
    # Levelized equivalents over LIFE at the same discount rate: (a) the whole year-1 price rises with inflation only;
    # (b) the energy part tracks the central Henry Hub path (relative to the 2025 STEO average, $3.53), the rest inflation.
    # Reference prices are 2025 (2026 for retail); carry them to the 2027 COD at inflation before levelizing.
    w = FIN_CENTRAL['wacc']
    infl = level((1 + OM_ESC) ** np.arange(LIFE), w)
    lag = {k: (1 + OM_ESC) ** (1 if k.startswith('EIA') else 2) for k in refs}
    hh = [v - DELIVERED_ADDER for v in list(gas_path('central').values())[:LIFE]]
    gas_idx = level(np.asarray(hh) / 3.53, w)
    energy_share = {'PJM wholesale + transmission, 2025 (IMM total price)': 49.28 / 82.67,
                    'PJM same, capacity at 2026/27 BRA, 80% LF': 49.28 / (82.67 - 13.09 + cap_2627),
                    'ERCOT wholesale all-in, 2025 (IMM: 2024 $34 x 1.138)': 1.0}
    out = []
    for k, v in refs.items():
        e = energy_share.get(k, np.nan)
        out.append(dict(reference=k, observed=v, levelized_inflation_only=v * lag[k] * infl,
                        levelized_gas_indexed=v * (e * gas_idx + (1 - e) * lag[k] * infl) if e == e else np.nan))
    return pd.DataFrame(out)


def bridge_lease(lease_kw_month=158.342e6 / (950e3 * 3), lf=0.80, site_mw=300):
    """Leased bridge power: Solaris Power Solutions Q2 2026 revenue ($158.3M) over ~950 MW earning revenue, per kW-month,
    plus fuel at the 2027 delivered strip. Fleet average incl. services/ancillary revenue; assumes the customer buys fuel."""
    tech = 'Simple-cycle turbines'
    n, m = units_needed(site_mw, TECH[tech]['unit_mw'], TECH[tech]['avail'])
    fuel = CASES[tech][0] * gas_path('central')[COD]
    rows = []
    for basis, over in (('leased MW = peak', 1.0), ('leased MW = peak x N+k', m / n)):
        cap = lease_kw_month * 12 * over / (8.76 * lf)
        rows.append(dict(basis=basis, lease_kw_month=lease_kw_month, capacity=cap / (1 - BTM_LOSS), fuel=fuel / (1 - BTM_LOSS),
                         total=(cap + fuel) / (1 - BTM_LOSS)))
    return pd.DataFrame(rows)


def main():
    pd.set_option('display.width', 250, 'display.max_columns', 30, 'display.max_rows', 200)
    laz = lazard_check()
    print('Lazard reproduction (published vs ours):')
    print(laz.round(2).to_string(index=False))

    rows = []
    for tech in TECH:
        for site in (100, 300, 1000):
            for system in (False, True):
                parts, meta = case_lcoe(tech, site, system=system, parts=True)
                lo = case_lcoe(tech, site, system=system, capex_case=1)
                hi = case_lcoe(tech, site, system=system, capex_case=2)
                rows.append(dict(tech=tech, site_mw=site, basis='system (N+k)' if system else 'bare', **meta,
                                 lcoe=sum(parts.values()), lcoe_capex_low=lo, lcoe_capex_high=hi, **parts))
    main_t = pd.DataFrame(rows).fillna(0.0)
    main_t.to_csv(OUT / 'lcoe_main.csv', index=False, float_format='%.3f')
    print(main_t.round(2).to_string(index=False))

    # one-at-a-time sensitivities, 300 MW site, system basis
    tests = {
        'central': {},
        'bare plant (no spares)': dict(system=False),
        'capex low': dict(capex_case=1), 'capex high': dict(capex_case=2),
        'gas: Waha (Permian) basis': dict(gas='waha'),
        'gas: AEO2026 path': dict(gas='aeo2026'),
        'gas: strip, then inflation only': dict(gas='strip_flat'),
        'WACC 6% / 10% (after tax)': None,
        'Lazard tax (40%)': dict(fin=FIN_LAZARD),
        '100% bonus depreciation (OBBBA)': dict(macrs='bonus'),
        'life 30 yr': dict(life=30),
        'bridge: 5-yr write-off': dict(life=5),
        'bridge: 10-yr write-off': dict(life=10),
        'load factor 0.70': dict(lf=0.70), 'load factor 0.90': dict(lf=0.90),
        'reliability 99.9%': dict(target=0.999), 'unit availability +2 pts': 'avail+',
        'part-load heat rate +5%': dict(hr_mult=1.05),
        'property tax + insurance 1.5%/yr of capex': dict(ptax=0.015),
        'carrying cost as Brattle CT (installed/overnight 1.28)': dict(idc_mult=2368 / 1853),
        'BESS 0.25 MW per MW peak': dict(bess_frac=0.25),
        'fuel cells: 30% ITC (48E(j))': dict(itc=0.30),
        'fuel cells: no stack replacement': dict(stack=0.0),
        'recips: 10 MW units': dict(unit_mw=10.0),
    }
    srows = []
    for tech in TECH:
        base = case_lcoe(tech)
        for name, kw in tests.items():
            if name.startswith('fuel cells') and not tech.startswith('Fuel'):
                continue
            if name.startswith('recips') and not tech.startswith('Recip'):
                continue
            if kw is None:
                vals = [case_lcoe(tech, fin=dict(wacc=x, tax=FIN_CENTRAL['tax'])) for x in (0.06, 0.10)]
                srows.append(dict(tech=tech, test=name, lcoe=f'{vals[0]:.0f} / {vals[1]:.0f}', delta=f'{vals[0]-base:+.0f} / {vals[1]-base:+.0f}'))
                continue
            if kw == 'avail+':
                kw = dict(avail=TECH[tech]['avail'] + 0.02)
            v = case_lcoe(tech, **kw)
            srows.append(dict(tech=tech, test=name, lcoe=f'{v:.0f}', delta=f'{v-base:+.0f}'))
    sens = pd.DataFrame(srows)
    sens.to_csv(OUT / 'lcoe_sensitivities.csv', index=False)
    print(sens.to_string(index=False))

    bl = bridge_lease()
    bl.to_csv(OUT / 'bridge_lease.csv', index=False, float_format='%.2f')
    print(bl.round(1).to_string(index=False))

    g = grid_refs()
    g.to_csv(OUT / 'grid_references.csv', index=False, float_format='%.1f')
    print(g.round(1).to_string(index=False))
    gp = gas_path('central')
    print('gas central path (delivered, nominal):', {y: round(gp[y], 2) for y in list(gp)[:22:3]})
    g20 = list(gp.values())[:LIFE]
    print('delivered gas, undiscounted 20-yr mean vs levelized:', round(np.mean(g20), 2), round(level(g20, FIN_CENTRAL['wacc']), 2))
    print('levelized delivered gas $/MMBtu, central / waha / aeo2026:',
          [round(level(list(gas_path(c).values())[:LIFE], FIN_CENTRAL['wacc']), 2) for c in ('central', 'waha', 'aeo2026', 'strip_flat')])


if __name__ == '__main__':
    main()
