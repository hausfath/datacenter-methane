"""BTM gas vs grid: case table, pre-registered decision table, break-even leak rates, within-cell Monte Carlo, sensitivities.

Parameters are frozen in PLAN.md §11 (fixed before this script was first run).
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import brentq

import emissions as em

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results'
OUT.mkdir(exist_ok=True)
GRID = json.load(open(ROOT / 'data/grid_inputs.json'))

# ---------------------------------------------------------------- parameters (PLAN.md §11)
CASES = {   # name: (HR central HHV MMBtu/MWh, (lo, hi), slip kg CH4/MMBtu, primary?)
    'Recip engines (lean-burn)': (8.40, (7.70, 8.85), 0.522, True),
    'Simple-cycle turbines': (9.80, (9.2, 11.0), 0.004, True),
    'Fuel cells (Bloom SOFC)': (6.40, (5.81, 7.13), 0.0, True),
    'Combined cycle (on site)': (6.60, (6.4, 7.0), 0.004, True),
    'Small rich-burn gensets': (11.6, (11.0, 12.5), 0.045, False),
}
GRID_NGCC_HR, GRID_NGCC_RANGE = 6.20, (6.1, 6.4)
SLIP_RANGE_RECIP = (0.24, 0.65)        # ~1.3-3.5% of CH4 (measured range, lit scan)
BTM_LOSS, GRID_LOSS = 0.01, 0.03
CMM = 0.199                            # kg CH4 / MMBtu coal (EPA GHGI 2023 / EIA 2023 consumption)
F_SUPPLY = 0.093
L_PRIMARY = 0.023
LEAKS = {'Low-leak supply (0.5%)': 0.005, 'National measured (2.3%)': 0.023, 'Sherwin six-region (2.43%)': 0.0243,
         'Permian (3.1%)': 0.031, 'Irzak Permian (4%)': 0.04, 'NM Permian 2018-20 (9.4%)': 0.094}
REGIONS = ['ERCOT', 'PJM', 'US']
TIE = 0.05


# ---------------------------------------------------------------- intensities
def btm(case, L, gwp='AR6_100', co2_only=False, hr=None, slip=None, fac=0.0, f=F_SUPPLY, mass_frac=em.CH4_MASS_FRAC,
        gwp_ch4=None, loss=BTM_LOSS):
    h0, _, s0, _ = CASES[case]
    p = em.intensity(h0 if hr is None else hr, s0 if slip is None else slip, L, gwp=gwp, supply_co2_frac=f, fac=fac,
                     mass_frac=mass_frac, parts=True)
    if gwp_ch4 is not None:
        scale = gwp_ch4 / em.GWP[gwp]['ch4']
        for k in ('ch4_slip', 'ch4_upstream', 'ch4_facility'):
            p[k] *= scale
    if co2_only:
        p = {k: v for k, v in p.items() if k.startswith('co2')}
    return {k: v / (1 - loss) for k, v in p.items()}


def grid_avg(region, L, gwp='AR6_100', co2_only=False, f=F_SUPPLY, mass_frac=em.CH4_MASS_FRAC, gwp_ch4=None,
             loss=GRID_LOSS, cmm=CMM, sub=None):
    g = GRID['egrid'][sub or region]
    gch4 = em.GWP[gwp]['ch4'] if gwp_ch4 is None else gwp_ch4
    p = dict(co2_combustion=g['co2_kg_mwh'] if co2_only else g['co2e_kg_mwh'],
             co2_supply=g['gas_mmbtu_per_mwh'] * em.EF_CO2 * f)
    if not co2_only:
        p['ch4_upstream'] = g['gas_mmbtu_per_mwh'] * em.upstream_ch4(L, mass_frac) * gch4
        p['ch4_coal_mine'] = g['coal_mmbtu_per_mwh'] * cmm * gch4
    return {k: v / (1 - loss) for k, v in p.items()}


def grid_ngcc(L, gwp='AR6_100', co2_only=False, hr=GRID_NGCC_HR, f=F_SUPPLY, mass_frac=em.CH4_MASS_FRAC, gwp_ch4=None,
              loss=GRID_LOSS):
    p = em.intensity(hr, 0.004, L, gwp=gwp, supply_co2_frac=f, mass_frac=mass_frac, parts=True)
    if gwp_ch4 is not None:
        scale = gwp_ch4 / em.GWP[gwp]['ch4']
        for k in ('ch4_slip', 'ch4_upstream'):
            p[k] *= scale
    if co2_only:
        p = {k: v for k, v in p.items() if k.startswith('co2')}
    return {k: v / (1 - loss) for k, v in p.items()}


tot = lambda d: sum(d.values())


def ref(name, region, L, **kw):
    return grid_avg(region, L, **kw) if name == 'A' else grid_ngcc(L, **kw)


def verdict(b, r):
    x = (b - r) / r
    return 'tied' if abs(x) < TIE else ('above' if x > 0 else 'below')


# ---------------------------------------------------------------- 1. case table
rows = []
for gwp in ['AR6_100', 'AR6_20']:
    for lname, L in LEAKS.items():
        for c in CASES:
            p = btm(c, L, gwp)
            rows.append(dict(kind='BTM', name=c, region='', leak=lname, L=L, gwp=gwp, total=tot(p), **p))
        for reg in REGIONS:
            p = grid_avg(reg, L, gwp)
            rows.append(dict(kind='grid A (average)', name=f'{reg} grid average', region=reg, leak=lname, L=L, gwp=gwp, total=tot(p), **p))
        p = grid_ngcc(L, gwp)
        rows.append(dict(kind='grid B (new NGCC)', name='New grid NGCC', region='', leak=lname, L=L, gwp=gwp, total=tot(p), **p))
cases = pd.DataFrame(rows).fillna(0.0)
cases.to_csv(OUT / 'cases.csv', index=False, float_format='%.2f')

# ---------------------------------------------------------------- 2. pre-registered decision table (primary cells)
dec = []
for reg in REGIONS:
    for rn in ['A', 'B']:
        for c, (_, _, _, prim) in CASES.items():
            b0, r0 = tot(btm(c, L_PRIMARY, co2_only=True)), tot(ref(rn, reg, L_PRIMARY, co2_only=True))
            b1, r1 = tot(btm(c, L_PRIMARY)), tot(ref(rn, reg, L_PRIMARY))
            dec.append(dict(region=reg, reference=rn, case=c, primary=prim,
                            btm_co2=b0, ref_co2=r0, gap_co2=b0 - r0, state_co2=verdict(b0, r0),
                            btm_full=b1, ref_full=r1, gap_full=b1 - r1, state_full=verdict(b1, r1),
                            gap_from_ch4=(b1 - r1) - (b0 - r0)))
dec = pd.DataFrame(dec)
dec.to_csv(OUT / 'decision_table.csv', index=False, float_format='%.1f')

# ---------------------------------------------------------------- 3. break-even matched leak rate L*
def lstar(case, rn, reg, gwp='AR6_100', **kw):
    g = lambda L: tot(btm(case, L, gwp, **kw)) - tot(ref(rn, reg, L, gwp=gwp))
    if g(0.0) >= 0:
        return 'none: above at L=0'
    if g(0.3) < 0:
        return '>30%'
    return round(brentq(g, 0.0, 0.3) * 100, 2)


be = []
for gwp in ['AR6_100', 'AR6_20']:
    for reg in REGIONS + ['sub_RFCE', 'sub_RFCW']:
        for rn in (['A', 'B'] if not reg.startswith('sub') else ['A']):
            for c in CASES:
                if rn == 'A' and reg.startswith('sub'):
                    g = lambda L, c=c: tot(btm(c, L, gwp)) - tot(grid_avg(None, L, gwp, sub=reg))
                    v = 'none: above at L=0' if g(0) >= 0 else ('>30%' if g(0.3) < 0 else round(brentq(g, 0, 0.3) * 100, 2))
                else:
                    v = lstar(c, rn, reg, gwp)
                be.append(dict(gwp=gwp, region=reg, reference=rn, case=c, L_star_pct=v))
# break-even facility leak (share of delivered CH4) for the efficient cases at L = 2.3%, ERCOT/PJM average
for c in ['Fuel cells (Bloom SOFC)', 'Combined cycle (on site)']:
    for reg in REGIONS:
        for rn in ['A', 'B']:
            g = lambda x: tot(btm(c, L_PRIMARY, fac=x)) - tot(ref(rn, reg, L_PRIMARY))
            v = 'none: above at 0' if g(0) >= 0 else round(brentq(g, 0, 0.5) * 100, 2)
            be.append(dict(gwp='AR6_100', region=reg, reference=rn, case=c + ' [facility leak*]', L_star_pct=v))
be = pd.DataFrame(be)
be.to_csv(OUT / 'breakeven.csv', index=False)

# ---------------------------------------------------------------- 4. within-cell correlated Monte Carlo (primary cells)
rng = np.random.default_rng(20261024)
N = 20000
L_d = np.clip(rng.normal(L_PRIMARY, 0.0035, N), 0.001, None)       # Alvarez 2.3% (+0.4/-0.3)
mf_d = rng.uniform(0.884, 0.970, N)
f_d = rng.uniform(0.08, 0.11, N)
gch4_d = np.clip(rng.normal(29.8, 11 / 1.645, N), 5, None)         # AR6 GWP100 fossil CH4 +/- 11 (5-95%)
loss_d = rng.uniform(0.02, 0.05, N)
mc = []
for c, (h0, (hlo, hhi), s0, prim) in CASES.items():
    hr_d = rng.uniform(hlo, hhi, N)
    slip_d = rng.uniform(*SLIP_RANGE_RECIP, N) if s0 > 0.1 else np.full(N, s0)
    ghr_d = rng.uniform(*GRID_NGCC_RANGE, N)
    b = np.array([tot(btm(c, L_d[i], hr=hr_d[i], slip=slip_d[i], f=f_d[i], mass_frac=mf_d[i], gwp_ch4=gch4_d[i]))
                  for i in range(N)])
    for reg in REGIONS:
        for rn in ['A', 'B']:
            if rn == 'A':
                r = np.array([tot(grid_avg(reg, L_d[i], f=f_d[i], mass_frac=mf_d[i], gwp_ch4=gch4_d[i], loss=loss_d[i])) for i in range(N)])
            else:
                r = np.array([tot(grid_ngcc(L_d[i], hr=ghr_d[i], f=f_d[i], mass_frac=mf_d[i], gwp_ch4=gch4_d[i], loss=loss_d[i])) for i in range(N)])
            rel = (b - r) / r
            mc.append(dict(region=reg, reference=rn, case=c, rel_gap_p05=np.percentile(rel, 5), rel_gap_p50=np.median(rel),
                           rel_gap_p95=np.percentile(rel, 95), p_btm_above=float((rel > 0).mean())))
mc = pd.DataFrame(mc)
mc['tie_band'] = np.maximum(TIE, (mc.rel_gap_p95 - mc.rel_gap_p05) / 2)   # PLAN §7: widen band to the MC 90% half-width
mc.to_csv(OUT / 'mc_primary_cells.csv', index=False, float_format='%.3f')

# decision table with the cell-specific (MC-widened) tie band, applied to both states
dec = dec.merge(mc[['region', 'reference', 'case', 'tie_band', 'p_btm_above']], on=['region', 'reference', 'case'])
band_verdict = lambda b, r, w: 'tied' if abs((b - r) / r) < w else ('above' if b > r else 'below')
dec['rel_gap_co2'] = dec.gap_co2 / dec.ref_co2
dec['rel_gap_full'] = dec.gap_full / dec.ref_full
dec['state_co2_band'] = [band_verdict(a, b, w) for a, b, w in zip(dec.btm_co2, dec.ref_co2, dec.tie_band)]
dec['state_full_band'] = [band_verdict(a, b, w) for a, b, w in zip(dec.btm_full, dec.ref_full, dec.tie_band)]
dec.to_csv(OUT / 'decision_table.csv', index=False, float_format='%.3f')

# ---------------------------------------------------------------- 5. one-at-a-time sensitivities (efficient cases)
sens = []
for c in ['Fuel cells (Bloom SOFC)', 'Combined cycle (on site)']:
    h0, (hlo, hhi), _, _ = CASES[c]
    for reg in ['ERCOT', 'PJM']:
        base = tot(btm(c, L_PRIMARY)) - tot(grid_avg(reg, L_PRIMARY))
        tests = {
            f'HR {hlo}': tot(btm(c, L_PRIMARY, hr=hlo)) - tot(grid_avg(reg, L_PRIMARY)),
            f'HR {hhi}': tot(btm(c, L_PRIMARY, hr=hhi)) - tot(grid_avg(reg, L_PRIMARY)),
            'L 0.5% both': tot(btm(c, 0.005)) - tot(grid_avg(reg, 0.005)),
            'L 3.1% both': tot(btm(c, 0.031)) - tot(grid_avg(reg, 0.031)),
            'BTM certified 0.5%, grid 2.3%': tot(btm(c, 0.005)) - tot(grid_avg(reg, L_PRIMARY)),
            'grid T loss 2%': tot(btm(c, L_PRIMARY)) - tot(grid_avg(reg, L_PRIMARY, loss=0.02)),
            'grid T&D 5%': tot(btm(c, L_PRIMARY)) - tot(grid_avg(reg, L_PRIMARY, loss=0.05)),
            'f 0.08': tot(btm(c, L_PRIMARY, f=0.08)) - tot(grid_avg(reg, L_PRIMARY, f=0.08)),
            'f 0.11': tot(btm(c, L_PRIMARY, f=0.11)) - tot(grid_avg(reg, L_PRIMARY, f=0.11)),
            'CH4 mass frac 0.884': tot(btm(c, L_PRIMARY, mass_frac=0.884)) - tot(grid_avg(reg, L_PRIMARY, mass_frac=0.884)),
            'CH4 mass frac 0.970': tot(btm(c, L_PRIMARY, mass_frac=0.970)) - tot(grid_avg(reg, L_PRIMARY, mass_frac=0.970)),
            'GWP20': tot(btm(c, L_PRIMARY, 'AR6_20')) - tot(grid_avg(reg, L_PRIMARY, 'AR6_20')),
            'CMM incl. abandoned (0.226)': tot(btm(c, L_PRIMARY)) - tot(grid_avg(reg, L_PRIMARY, cmm=0.226)),
        }
        if c.startswith('Fuel'):
            tests['Bloom lifetime avg 54% LHV (7.0)'] = tot(btm(c, L_PRIMARY, hr=7.0)) - tot(grid_avg(reg, L_PRIMARY))
        for k, v in tests.items():
            sens.append(dict(case=c, region=reg, test=k, gap_base=base, gap=v, ref=tot(grid_avg(reg, L_PRIMARY)),
                             rel_gap=v / tot(grid_avg(reg, L_PRIMARY))))
pd.DataFrame(sens).to_csv(OUT / 'sensitivities.csv', index=False, float_format='%.3f')

if __name__ == '__main__':
    pd.set_option('display.width', 250, 'display.max_columns', 30, 'display.max_rows', 200)
    print(dec[['region', 'reference', 'case', 'rel_gap_co2', 'rel_gap_full', 'tie_band', 'state_co2_band', 'state_full_band',
               'gap_from_ch4', 'p_btm_above']].round(3).to_string())
    print(be[(be.gwp == 'AR6_20')].to_string())
    s = pd.read_csv(OUT / 'sensitivities.csv')
    print(s[['case', 'region', 'test', 'rel_gap']].round(3).to_string())
