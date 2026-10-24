"""Fleet-scale FaIR runs: 300 TWh/yr for 2027-2046 from each supply option, at matched L = 2.3% (PLAN §8).

Per-MWh CO2 and CH4 masses come from cases.py functions (GWP-free masses). Fossil CH4 oxidation CO2 is added.
Writes results/fair_fleet.npz (ensemble-median and quantile time series) and results/fair_fleet.json.
"""
import json
from pathlib import Path

import numpy as np

import cases as cs
import fair_runs as fr

OUT = Path(__file__).resolve().parents[1] / 'results'
TWH = 300.0
Y0, Y1 = 2027, 2047
L = cs.L_PRIMARY
G = 29.8


def masses(parts):
    """kg CO2 and kg CH4 per MWh from an AR6_100 parts dict."""
    co2 = sum(v for k, v in parts.items() if k.startswith('co2'))
    ch4 = sum(v for k, v in parts.items() if k.startswith('ch4')) / G
    return co2, ch4


OPTIONS = {c: masses(cs.btm(c, L)) for c in cs.CASES if cs.CASES[c][3]}
OPTIONS['ERCOT grid average'] = masses(cs.grid_avg('ERCOT', L))
OPTIONS['PJM grid average'] = masses(cs.grid_avg('PJM', L))
OPTIONS['New grid NGCC'] = masses(cs.grid_ngcc(L))

tp = fr.timepoints()
on = (tp >= Y0) & (tp < Y1)
tb = np.arange(fr.START, fr.END + 1)
REPORT = [2035, 2050, 2100, 2150]


def series(co2_kg, ch4_kg, scale=1.0):
    mwh = TWH * 1e6 * scale
    ch4_mt = np.where(on, ch4_kg * mwh / 1e9, 0.0)
    co2_gt = np.where(on, co2_kg * mwh / 1e12, 0.0) + fr.with_oxidation(tp, ch4_mt)
    return co2_gt, ch4_mt


res, store = {'options_kg_per_mwh': {k: dict(co2=v[0], ch4=v[1]) for k, v in OPTIONS.items()}}, {}
for ssp in ['ssp126', 'ssp245', 'ssp370']:
    base, _ = fr.run(ssp)
    dT = {}
    for name, (co2, ch4) in OPTIONS.items():
        T, _ = fr.run(ssp, *series(co2, ch4))
        dT[name] = T - base
        print(ssp, name, f'{np.median(dT[name][tb == 2050]) * 1000:.2f} mK in 2050')
    # linearity: recip at half scale
    rc = 'Recip engines (lean-burn)'
    Th, _ = fr.run(ssp, *series(*OPTIONS[rc], scale=0.5))
    lin = np.median((Th - base)[tb == 2050] / dT[rc][tb == 2050])
    r = {'linearity_half_over_full_2050': float(lin)}
    for name in OPTIONS:
        d = dT[name] / TWH * 1000   # mK per TWh/yr sustained 20 yr
        r[name] = {str(y): [float(x) for x in np.percentile(d[tb == y][0], [5, 50, 95])] for y in REPORT}
        r[name]['peak_median_mK_per_TWh'] = float(np.median(d, axis=1).max())
        r[name]['peak_year'] = int(tb[np.argmax(np.median(d, axis=1))])
        store[f'{ssp}|{name}|q'] = np.percentile(d, [5, 50, 95], axis=1)
        for refn in ['ERCOT grid average', 'PJM grid average', 'New grid NGCC']:
            if name in cs.CASES:
                diff = (dT[name] - dT[refn]) / TWH * 1000
                ratio = dT[name] / dT[refn]
                r[name][f'minus {refn}'] = {str(y): [float(x) for x in np.percentile(diff[tb == y][0], [5, 50, 95])] for y in REPORT}
                r[name][f'ratio to {refn}'] = {str(y): [float(x) for x in np.percentile(ratio[tb == y][0], [5, 50, 95])] for y in REPORT}
                store[f'{ssp}|{name}|ratio|{refn}'] = np.percentile(np.where(tb[:, None] >= Y0 + 1, ratio, np.nan), [5, 50, 95], axis=1)
    res[ssp] = r
np.savez_compressed(OUT / 'fair_fleet.npz', timebounds=tb, **store)
json.dump(res, open(OUT / 'fair_fleet.json', 'w'), indent=1)
print(json.dumps({k: res['ssp245'][k] for k in ['linearity_half_over_full_2050']}, indent=1))
