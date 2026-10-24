"""Regional sensitivity (PLAN_regional.md R2): BTM options vs each hotspot region's grid at the supplying basin's leak rate.

Grid A primary = EIA-930 2025 consumption-based CO2 intensity of the BA + gas upstream (f, CH4 at L) + regional coal-mine CH4
+ coal supply CO2, / (1 - transmission loss). Bracket: eGRID2023 BA production and subregion. B = new H-class NGCC on local gas.
Four-state classification with per-region MC tie bands. Main-analysis parameters are imported unchanged from cases.py.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import brentq

import cases as cs
import emissions as em

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results' / 'regional'
OUT.mkdir(parents=True, exist_ok=True)
J = json.load(open(ROOT / 'data' / 'basin_leak_rates.json'))
BASINS, REGIONS = J['basins'], J['regions_R2']
EIA = json.load(open(ROOT / 'data' / 'eia930_intensity.json'))
EG = cs.GRID['egrid']
CAMB = cs.GRID['cambium_lrmer_gea_2027_2046']
GEA = {'West Texas': 'ERCOT', 'Texas Panhandle': 'SPP_South', 'El Paso / S. NM': 'WestConnect_South', 'PJM': 'PJM_West',
       'Memphis': 'SERTP', 'Cheyenne': 'WestConnect_North', 'Central Utah': 'NorthernGrid_South'}
EIA_YEAR = '2025'
EF_COAL = 96.0          # kg CO2/MMBtu, coal blend (EIA: bituminous 93.3, subbituminous 97.2, lignite 97.7)
PRIMARY = [c for c, v in cs.CASES.items() if v[3]]
CENTRAL = dict(mf=em.CH4_MASS_FRAC, f=cs.F_SUPPLY, gch4=29.8, loss=cs.GRID_LOSS, fc=0.02)


def grid_fuel(region, basis):
    """(combustion kg CO2(e)/MWh, gas MMBtu/MWh, coal MMBtu/MWh) for the grid basis."""
    r = REGIONS[region]
    if basis == 'EIA-930 consumption 2025':
        e = EIA[r['ba']][EIA_YEAR]
        cons = e['consumption_kg_mwh']
        return cons, cons * e['gas_share_gen_co2'] / em.EF_CO2, cons * e['coal_share_gen_co2'] / EF_COAL
    if basis == 'EIA-930 consumption 2023':
        e = EIA[r['ba']]['2023']
        cons = e['consumption_kg_mwh']
        return cons, cons * e['gas_share_gen_co2'] / em.EF_CO2, cons * e['coal_share_gen_co2'] / EF_COAL
    g = EG[r['egrid_ba'] if basis == 'eGRID 2023 BA' else r['egrid_sub']]
    return g['co2e_kg_mwh'], g['gas_mmbtu_per_mwh'], g['coal_mmbtu_per_mwh']


def up(L, mf):
    return em.KG_NG_PER_MMBTU * mf * L / (1 - L)


def btm(case, L, mf, f, gch4, hr=None, slip=None, co2_only=False, gn2o=273.0):
    h0, _, s0, _ = cs.CASES[case]
    hr = h0 if hr is None else hr
    slip = s0 if slip is None else slip
    co2 = hr * em.EF_CO2 * (1 + f)
    if co2_only:
        return co2 / (1 - cs.BTM_LOSS)
    return (co2 + hr * gch4 * (slip + up(L, mf)) + hr * 1e-4 * gn2o) / (1 - cs.BTM_LOSS)


def grid_A(region, L, mf, f, gch4, loss, cmm, fc, basis='EIA-930 consumption 2025', co2_only=False):
    comb, gas, coal = grid_fuel(region, basis)
    co2 = comb + gas * em.EF_CO2 * f + coal * EF_COAL * fc
    if co2_only:
        return co2 / (1 - loss)
    return (co2 + gas * gch4 * up(L, mf) + coal * cmm * gch4) / (1 - loss)


def grid_B(L, mf, f, gch4, loss, co2_only=False, hr=cs.GRID_NGCC_HR, gn2o=273.0):
    co2 = hr * em.EF_CO2 * (1 + f)
    if co2_only:
        return co2 / (1 - loss)
    return (co2 + hr * gch4 * (0.004 + up(L, mf)) + hr * 1e-4 * gn2o) / (1 - loss)


# ---------------------------------------------------------------- per-region MC tie bands (matched pairing, GWP100)
rng = np.random.default_rng(20261024)
N = 20000
bands, mcrows = {}, []
for reg, r in REGIONS.items():
    lo, mid, hi = BASINS[r['basin']]['L']
    L = rng.triangular(lo, mid, hi, N)
    mf = rng.uniform(0.884, 0.970, N); f = rng.uniform(0.08, 0.11, N)
    g = np.clip(rng.normal(29.8, 11 / 1.645, N), 5, None); loss = rng.uniform(0.02, 0.05, N)
    cmm = rng.uniform(r['cmm'][0], r['cmm'][2], N); fc = rng.uniform(0.01, 0.03, N)
    A = grid_A(reg, L, mf, f, g, loss, cmm, fc)
    ghr = rng.uniform(*cs.GRID_NGCC_RANGE, N)
    B = grid_B(L, mf, f, g, loss, hr=ghr)
    for c, (h0, (hlo, hhi), s0, _) in cs.CASES.items():
        hr = rng.uniform(hlo, hhi, N)
        slip = rng.uniform(*cs.SLIP_RANGE_RECIP, N) if s0 > 0.1 else np.full(N, s0)
        b = btm(c, L, mf, f, g, hr=hr, slip=slip)
        for ref, R in (('A', A), ('B', B)):
            rel = (b - R) / R
            p05, p50, p95 = np.percentile(rel, [5, 50, 95])
            bands[(reg, c, ref)] = max(cs.TIE, (p95 - p05) / 2)
            mcrows.append(dict(region=reg, case=c, reference=ref, rel_p05=p05, rel_p50=p50, rel_p95=p95,
                               p_above=float((rel > 0).mean()), band=bands[(reg, c, ref)]))
pd.DataFrame(mcrows).to_csv(OUT / 'regional_mc.csv', index=False, float_format='%.4f')


def state(vA, vB):
    if vA == 'tied' and vB == 'tied':
        return 'Tied'
    if vA == 'above' and vB == 'above':
        return 'Worse'
    if vA == 'below' and vB == 'below':
        return 'Better'
    if vA in ('below', 'tied') and vB in ('below', 'tied'):     # gap in PLAN_regional §5 definitions; labelled explicitly
        return 'Below A, tied B' if vA == 'below' else 'Tied A, below B'
    return 'Between (above A)' if vA == 'above' else 'Between (above B)'


def v(b, R, w):
    x = (b - R) / R
    return 'tied' if abs(x) < w else ('above' if x > 0 else 'below')


# ---------------------------------------------------------------- deterministic variants
rows = []
for reg, r in REGIONS.items():
    bas = BASINS[r['basin']]
    lo, mid, hi = bas['L']
    alloc = bas['gas_boe_share']
    variants = [('matched', 'central', mid, mid, 'EIA-930 consumption 2025', 'AR6_100', 29.8),
                ('matched', 'low', lo, lo, 'EIA-930 consumption 2025', 'AR6_100', 29.8),
                ('matched', 'high', hi, hi, 'EIA-930 consumption 2025', 'AR6_100', 29.8),
                ('local BTM, national grid gas', 'central', mid, cs.L_PRIMARY, 'EIA-930 consumption 2025', 'AR6_100', 29.8),
                ('local BTM, national grid gas', 'low', lo, cs.L_PRIMARY, 'EIA-930 consumption 2025', 'AR6_100', 29.8),
                ('local BTM, national grid gas', 'high', hi, cs.L_PRIMARY, 'EIA-930 consumption 2025', 'AR6_100', 29.8),
                ('energy-allocated', 'central', mid * alloc, mid * alloc, 'EIA-930 consumption 2025', 'AR6_100', 29.8),
                ('matched', 'central', mid, mid, 'EIA-930 consumption 2023', 'AR6_100', 29.8),
                ('matched', 'central', mid, mid, 'eGRID 2023 BA', 'AR6_100', 29.8),
                ('matched', 'central', mid, mid, 'eGRID 2023 subregion', 'AR6_100', 29.8),
                ('matched', 'central', mid, mid, 'EIA-930 consumption 2025', 'AR6_20', 82.5)]
    for pairing, lev, Lb, Lg, basis, gwp, gch4 in variants:
        gn2o = 273.0
        A1 = grid_A(reg, Lg, CENTRAL['mf'], CENTRAL['f'], gch4, CENTRAL['loss'], r['cmm'][1], CENTRAL['fc'], basis)
        A0 = grid_A(reg, Lg, CENTRAL['mf'], CENTRAL['f'], gch4, CENTRAL['loss'], r['cmm'][1], CENTRAL['fc'], basis, co2_only=True)
        B1 = grid_B(Lb, CENTRAL['mf'], CENTRAL['f'], gch4, CENTRAL['loss'])
        B0 = grid_B(Lb, CENTRAL['mf'], CENTRAL['f'], gch4, CENTRAL['loss'], co2_only=True)
        for c in cs.CASES:
            b1 = btm(c, Lb, CENTRAL['mf'], CENTRAL['f'], gch4, gn2o=gn2o)
            b0 = btm(c, Lb, CENTRAL['mf'], CENTRAL['f'], gch4, co2_only=True)
            wA, wB = bands[(reg, c, 'A')], bands[(reg, c, 'B')]
            vA, vB, vA0, vB0 = v(b1, A1, wA), v(b1, B1, wB), v(b0, A0, wA), v(b0, B0, wB)
            rows.append(dict(region=reg, label=r['label'], case=c, primary_case=c in cs.CASES and cs.CASES[c][3],
                             pairing=pairing, L_level=lev, L_btm=Lb, L_grid=Lg, grid_basis=basis, gwp=gwp,
                             btm=b1, A=A1, B=B1, rel_A=(b1 - A1) / A1, rel_B=(b1 - B1) / B1,
                             rel_A_co2=(b0 - A0) / A0, rel_B_co2=(b0 - B0) / B0, band_A=wA, band_B=wB,
                             vA=vA, vB=vB, state=state(vA, vB), state_co2=state(vA0, vB0),
                             worse_than_grid=(vA == 'above') and (vB == 'above'),
                             cambium_lrmer_mid=CAMB[GEA[reg]]['Mid-case'],
                             cambium_lrmer_range=[min(CAMB[GEA[reg]].values()), max(CAMB[GEA[reg]].values())]))
df = pd.DataFrame(rows)
df.to_csv(OUT / 'regional_cases.csv', index=False, float_format='%.4f')

# ---------------------------------------------------------------- break-even matched L* (central otherwise)
be = []
for reg, r in REGIONS.items():
    for c in cs.CASES:
        for ref in ('A', 'B'):
            def gap(L):
                R = grid_A(reg, L, CENTRAL['mf'], CENTRAL['f'], 29.8, CENTRAL['loss'], r['cmm'][1], CENTRAL['fc']) if ref == 'A' \
                    else grid_B(L, CENTRAL['mf'], CENTRAL['f'], 29.8, CENTRAL['loss'])
                return btm(c, L, CENTRAL['mf'], CENTRAL['f'], 29.8) - R
            g0, g1 = gap(0.0), gap(0.2)
            if g0 >= 0 and g1 >= 0:
                val = 'BTM above at all L (0-20%)'
            elif g0 < 0 and g1 < 0:
                val = 'BTM below at all L (0-20%)'
            else:
                val = round(brentq(gap, 0.0, 0.2) * 100, 2)
            be.append(dict(region=reg, case=c, reference=ref, L_star_pct=val,
                           basin_low_mid_high_pct=[round(x * 100, 2) for x in BASINS[r['basin']]['L']],
                           btm_rises_faster=bool(gap(0.05) > gap(0.0))))
pd.DataFrame(be).to_csv(OUT / 'regional_breakeven.csv', index=False)

if __name__ == '__main__':
    pd.set_option('display.width', 260, 'display.max_rows', 500, 'display.max_columns', 30)
    p = df[(df.pairing == 'matched') & (df.L_level == 'central') & (df.grid_basis == 'EIA-930 consumption 2025') & (df.gwp == 'AR6_100')]
    print(p[['region', 'case', 'btm', 'A', 'B', 'rel_A', 'rel_B', 'rel_A_co2', 'band_A', 'band_B', 'state', 'state_co2']].round(3).to_string())
