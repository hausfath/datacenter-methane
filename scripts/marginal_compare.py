"""Assemble every grid metric (PLAN_marginal v2) and classify each off-grid option against it.

Inputs: results/marginal/srmer_primary.csv, cambium_matched.csv, build_margins.csv; cases.py for the posted averages,
new NGCC and the off-grid values. Writes results/marginal/grid_definitions.csv and verdicts.csv.
Decision rule: band = max(5%, main-analysis MC tie band, half-width of the metric's range); worse / tie / better.
"""
from pathlib import Path

import numpy as np
import pandas as pd

import json

import emissions as em
from cases import CASES, CMM, F_SUPPLY, GRID_LOSS, L_PRIMARY, btm, grid_avg, grid_ngcc, tot

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / 'results' / 'marginal'
YEAR = 2025
W, W_RANGE = 0.25, (0.15, 0.35)
CAMBIUM_GEA = {'ERCOT': 'ERCOT', 'PJM': 'PJM_East', 'US': 'US (pop-weighted)'}
OPTIONS = [c for c, v in CASES.items() if v[3]]


def average_2025(reg, ef_coal=96.0):
    """Same-vintage grid average: EIA-930 2025 consumption CO2 intensity (data/eia930_intensity.json) with the
    main analysis's upstream gas CH4, supply CO2 and coal-mine CH4, /(1 - 0.03). Not available for the US."""
    ba = {'ERCOT': 'ERCO', 'PJM': 'PJM'}.get(reg)
    if ba is None:
        return np.nan
    e = json.load(open(ROOT / 'data' / 'eia930_intensity.json'))[ba]['2025']
    c = e['consumption_kg_mwh']
    gas, coal = c * e['gas_share_gen_co2'] / em.EF_CO2, c * e['coal_share_gen_co2'] / ef_coal
    g = em.GWP['AR6_100']['ch4']
    return (c + gas * em.EF_CO2 * F_SUPPLY + gas * em.upstream_ch4(L_PRIMARY) * g + coal * CMM * g) / (1 - GRID_LOSS)


def metrics():
    sr = pd.read_csv(R / 'srmer_primary.csv')
    cam = pd.read_csv(R / 'cambium_matched.csv')
    bm = pd.read_csv(R / 'build_margins.csv')
    rows = []
    for reg in ('ERCOT', 'PJM', 'US'):
        avg = tot(grid_avg(reg, L_PRIMARY))
        rows.append(dict(region=reg, metric='average', label='Grid average (as in the post)', horizon='today',
                         central=avg, lo=np.nan, hi=np.nan, note='eGRID2023, 3% losses'))
        s = sr[(sr.year == YEAR) & (sr.region == reg)].iloc[0]
        rows.append(dict(region=reg, metric='srmer', label="Short-run marginal (today's grid)", horizon='short',
                         central=s.srmer_delivered, lo=s.env_min, hi=s.env_max, ci05=s.ci05, ci95=s.ci95,
                         note=f'{YEAR} CEMS + EIA-930, levels + FE, 6% marginal losses; bar = specification envelope'))
        c = cam[(cam.gea == CAMBIUM_GEA[reg]) & (cam.discount == 0.03)]
        lr = float(c[c.scenario == 'High Demand Growth'].matched.iloc[0])
        rows.append(dict(region=reg, metric='cambium', label='Long-run marginal (NREL Cambium 2024)', horizon='long',
                         central=lr, lo=c.matched.min(), hi=c.matched.max(),
                         note=f'{CAMBIUM_GEA[reg]}, High Demand Growth, 2027-2046 levelized 3%; bar = 8 scenarios; pre-OBBBA'))
        rows.append(dict(region=reg, metric='blend', label='Blend: 5 years short-run, then long-run', horizon='blend',
                         central=W * s.srmer_delivered + (1 - W) * lr,
                         lo=W_RANGE[0] * s.srmer_delivered + (1 - W_RANGE[0]) * lr,
                         hi=W_RANGE[1] * s.srmer_delivered + (1 - W_RANGE[1]) * lr,
                         note='Gagnon & O\'Shaughnessy 2024; w = 0.25 (0.15-0.35)'))
        b = bm[bm.region == reg].set_index('metric').value
        pc, pa = b['planned additions 2026-2030 (under construction)'], b['planned additions 2026-2030 (all statuses)']
        rows.append(dict(region=reg, metric='planned', label='Planned additions 2026-30 (average)', horizon='long',
                         central=pa, lo=min(pc, pa), hi=max(pc, pa),
                         note='EIA-860M Sep 2026; central = all statuses, bar to under-construction only'))
        rt, rw = b['recent additions (Tool 07 20% sample)'], b['recent additions (online 2020-2024)']
        rows.append(dict(region=reg, metric='recent', label='Recent additions (average)', horizon='long',
                         central=rt, lo=min(rt, rw), hi=max(rt, rw), note='Tool 07 20% sample; bar to 2020-24 window'))
        rows.append(dict(region=reg, metric='ngcc', label='New gas plant on the grid', horizon='long',
                         central=tot(grid_ngcc(L_PRIMARY)), lo=np.nan, hi=np.nan, note='H-class NGCC, 3% losses'))
        rows.append(dict(region=reg, metric='average_2025', label='Grid average, 2025 (same vintage as the short-run rate)',
                         horizon='today', central=average_2025(reg), lo=np.nan, hi=np.nan,
                         note='table only: EIA-930 2025 consumption-basis CO2 with the main analysis upstream terms; no US aggregate in EIA-930 intensities'))
    return pd.DataFrame(rows)


def verdicts(m):
    """band = max(5%, main-analysis Monte Carlo tie band for this option and region, half-width of the metric's range).
    The Monte Carlo band carries the off-grid side's own uncertainty (heat rate, slip, leakage draws), which does not
    depend on how the grid is counted; for the average and new-NGCC rows this reproduces the post's verdicts."""
    mc = pd.read_csv(ROOT / 'results' / 'decision_table.csv')
    mc = mc.set_index(['region', 'reference', 'case']).tie_band
    out = []
    for _, r in m.iterrows():
        if np.isnan(r.central):
            continue
        half = np.nanmax([r.central - r.lo, r.hi - r.central]) / r.central if not np.isnan(r.lo) else 0.0
        for o in OPTIONS:
            band = max(0.05, half, mc[(r.region, 'B' if r.metric == 'ngcc' else 'A', o)])
            v = tot(btm(o, L_PRIMARY))
            ratio = v / r.central
            out.append(dict(region=r.region, metric=r.metric, option=o, offgrid=v, grid=r.central, ratio=ratio, band=band,
                            verdict='worse' if ratio > 1 + band else 'better' if ratio < 1 - band else 'tie'))
    return pd.DataFrame(out)


if __name__ == '__main__':
    m = metrics()
    m.to_csv(R / 'grid_definitions.csv', index=False)
    v = verdicts(m)
    v.to_csv(R / 'verdicts.csv', index=False)
    with pd.option_context('display.width', 200):
        print(m[['region', 'metric', 'central', 'lo', 'hi']].round(0).to_string())
        print(v.pivot_table(index=['region', 'metric'], columns='option', values='ratio').round(2).to_string())
        print(v.pivot_table(index=['region', 'metric'], columns='option', values='verdict', aggfunc='first').to_string())
