"""Regional sensitivity (PLAN_regional.md): BTM options vs each hotspot region's grid, at the supplying basin's leak rate.

Reuses cases.py functions and parameters unchanged. Basin leak rates are fixed in PLAN_regional.md §6 before this runs.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

import cases as cs

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results' / 'regional'
OUT.mkdir(parents=True, exist_ok=True)

# basin: (low, central, high) loss as share of CH4 produced, whole basin, unallocated. Filled from BASINS.md (PLAN_regional §6).
BASINS = json.load(open(ROOT / 'data' / 'basin_leak_rates.json'))['basins']

# region: (label, primary grid key, [alternative grid keys], basin)
REGIONS = json.load(open(ROOT / 'data' / 'basin_leak_rates.json'))['regions']

PRIMARY = [c for c, v in cs.CASES.items() if v[3]]
ALL = list(cs.CASES)
L_NATIONAL = cs.L_PRIMARY

# tie band per prime mover: largest MC-widened band vs reference A across the main analysis's three regions
mc = pd.read_csv(ROOT / 'results' / 'mc_primary_cells.csv')
BAND = mc[mc.reference == 'A'].groupby('case').tie_band.max().to_dict()
BAND_B = mc[mc.reference == 'B'].groupby('case').tie_band.max().to_dict()


def verdict(b, r, w):
    x = (b - r) / r
    return 'tied' if abs(x) < w else ('above' if x > 0 else 'below')


rows = []
for rkey, reg in REGIONS.items():
    lo, mid, hi = BASINS[reg['basin']]['L']
    for grid_key in [reg['grid']] + reg['alt_grids']:
        for pairing, Lb, Lg in [('matched', mid, mid), ('matched-low', lo, lo), ('matched-high', hi, hi),
                                ('local BTM, national grid gas', mid, L_NATIONAL),
                                ('local BTM low, national grid gas', lo, L_NATIONAL),
                                ('local BTM high, national grid gas', hi, L_NATIONAL)]:
            for gwp in ['AR6_100', 'AR6_20']:
                for c in ALL:
                    b0 = cs.tot(cs.btm(c, Lb, gwp, co2_only=True))
                    b1 = cs.tot(cs.btm(c, Lb, gwp))
                    a0 = cs.tot(cs.grid_avg(None, Lg, gwp, co2_only=True, sub=grid_key))
                    a1 = cs.tot(cs.grid_avg(None, Lg, gwp, sub=grid_key))
                    n0 = cs.tot(cs.grid_ngcc(Lg, gwp, co2_only=True))
                    n1 = cs.tot(cs.grid_ngcc(Lg, gwp))
                    wA, wB = BAND.get(c, cs.TIE), BAND_B.get(c, cs.TIE)
                    rows.append(dict(region=rkey, region_label=reg['label'], grid=grid_key, grid_primary=grid_key == reg['grid'],
                                     basin=reg['basin'], pairing=pairing, L_btm=Lb, L_grid=Lg, gwp=gwp, case=c,
                                     primary_case=c in PRIMARY, btm=b1, gridA=a1, gridB=n1,
                                     rel_A=(b1 - a1) / a1, rel_B=(b1 - n1) / n1, rel_A_co2=(b0 - a0) / a0, rel_B_co2=(b0 - n0) / n0,
                                     vA=verdict(b1, a1, wA), vB=verdict(b1, n1, wB), vA_co2=verdict(b0, a0, wA), vB_co2=verdict(b0, n0, wB),
                                     band_A=wA, band_B=wB))
df = pd.DataFrame(rows)
df['worse_than_grid'] = (df.vA == 'above') & (df.vB == 'above')
df['worse_than_grid_co2'] = (df.vA_co2 == 'above') & (df.vB_co2 == 'above')
df.to_csv(OUT / 'regional_cases.csv', index=False, float_format='%.4f')

# break-even matched L* vs primary regional grid A
be = []
for rkey, reg in REGIONS.items():
    for c in ALL:
        g = lambda L: cs.tot(cs.btm(c, L)) - cs.tot(cs.grid_avg(None, L, sub=reg['grid']))
        if g(0.0) >= 0:
            v = 'above at L=0'
        elif g(0.3) < 0:
            v = 'below up to L=30%'
        else:
            from scipy.optimize import brentq
            v = round(brentq(g, 0, 0.3) * 100, 2)
        be.append(dict(region=rkey, case=c, L_star_vs_A_pct=v, basin_range_pct=[x * 100 for x in BASINS[reg['basin']]['L']]))
pd.DataFrame(be).to_csv(OUT / 'regional_breakeven.csv', index=False)

if __name__ == '__main__':
    pd.set_option('display.width', 250, 'display.max_rows', 400)
    p = df[(df.grid_primary) & (df.pairing == 'matched') & (df.gwp == 'AR6_100')]
    print(p[['region', 'case', 'btm', 'gridA', 'gridB', 'rel_A', 'rel_B', 'vA_co2', 'vA', 'vB', 'worse_than_grid']].round(3).to_string())
    print(pd.DataFrame(be).to_string())
