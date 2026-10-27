"""M2: Cambium 2024 long-run marginal emission rates on this project's accounting (PLAN_marginal §M2).

Matched reconstruction: back out marginal gas (G) and coal (C) heat input per MWh from Cambium's combustion CO2 and CH4
(CO2 = 53.06 G + 95.52 C kg; CH4 = 1.0 G + 11.0 C g), then rebuild CO2e with upstream CH4 at L, supply CO2 f and
coal-mine CH4, as grid_avg() does. End-use -> busbar with Cambium's distribution loss rate, then /(1 - 0.03).

Validations: (1) our levelization reproduces the workbook's cached levelized combustion CO2 (Mid-case, 2025, 20 yr, 3%);
(2) reconstructed G and C reproduce Cambium's own precombustion CO2 (6.27 G + 2.94 C kg) within 3% (ERCOT, PJM_East).
Writes results/marginal/cambium_matched.csv and cambium_validation.json.
"""
import json
from pathlib import Path

import numpy as np
import openpyxl
import pandas as pd

import emissions as em
from cases import CMM, F_SUPPLY, GRID_LOSS, L_PRIMARY

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results' / 'marginal'
OUT.mkdir(parents=True, exist_ok=True)
WB = ROOT / 'data/cambium/Cambium24_Workbook.xlsx'
BLOCKS = dict(co2c=15, ch4c=63, n2oc=111, co2p=159, ch4p=207, n2op=255)
EF_COAL_CO2, EF_GAS_CH4, EF_COAL_CH4 = 95.52, 1.0, 11.0   # kg CO2 / g CH4 per MMBtu (Cambium documentation Table 5)
PRE_CO2 = dict(gas=6.27, coal=2.94)                         # Cambium precombustion CO2, kg/MMBtu
G = em.GWP['AR6_100']


def load():
    wb = openpyxl.load_workbook(WB, read_only=True, data_only=True)
    rows = list(wb['Data - Annual'].iter_rows(values_only=True))
    scen_row, year_row = rows[3], rows[4]
    scen = [scen_row[15 + 6 * k] for k in range(8)]
    yrs = np.array(year_row[15:21], dtype=float)
    data = {}
    for r in rows[5:]:
        if not r[1]:
            continue
        for k, s in enumerate(scen):
            data[(r[1], s)] = {b: np.array(r[c + 6 * k:c + 6 * k + 6], dtype=float) for b, c in BLOCKS.items()}
            data[(r[1], s)]['dist_loss'] = r[303]
    cached = [x for x in list(wb['Levelized LRMER'].iter_rows(min_row=20, max_row=22, values_only=True))]
    cached = {name: val for name, val in zip(cached[0], cached[2]) if name and name != 'Outputs'}
    return data, scen, yrs, cached


def decompose(d):
    """Gas and coal MMBtu per MWh end-use at the 5-year points."""
    A = np.array([[em.EF_CO2, EF_COAL_CO2], [EF_GAS_CH4, EF_COAL_CH4]])
    gc = np.linalg.solve(A, np.vstack([d['co2c'], d['ch4c']]))
    return np.clip(gc[0], 0, None), np.clip(gc[1], 0, None)


def matched_co2e(d, L=L_PRIMARY):
    gas, coal = decompose(d)
    return (d['co2c'] + d['ch4c'] / 1000 * G['ch4'] + d['n2oc'] / 1000 * G['n2o']
            + gas * em.EF_CO2 * F_SUPPLY + gas * em.upstream_ch4(L) * G['ch4'] + coal * CMM * G['ch4'])


def native_co2e(d):
    return (d['co2c'] + d['co2p'] + (d['ch4c'] + d['ch4p']) / 1000 * G['ch4'] + (d['n2oc'] + d['n2op']) / 1000 * G['n2o'])


def levelize(series, yrs, start=2027, n=20, d=0.03):
    t = np.arange(start, start + n)
    w = 1 / (1 + d) ** (t - start)
    return float(np.sum(np.interp(t, yrs, series) * w) / np.sum(w))


def to_busbar(x, dist_loss):
    return x * (1 - dist_loss) / (1 - GRID_LOSS)


def us_weights():
    wb = openpyxl.load_workbook(WB, read_only=True, data_only=True)
    cm = pd.DataFrame(list(wb['County Mapping'].iter_rows(min_row=2, values_only=True))).iloc[:, :7]
    cm.columns = ['st', 'co', 'county', 'abbr', 'state', 'reeds', 'gea']
    pop = pd.read_csv(ROOT / 'data/marginal/county_pop_2024.csv')
    m = cm.merge(pop, left_on=['st', 'co'], right_on=['STATE', 'COUNTY'], how='left')
    miss = m.POPESTIMATE2024.isna().sum()
    w = m.groupby('gea').POPESTIMATE2024.sum()
    return (w / w.sum()).to_dict(), int(miss), float(m.POPESTIMATE2024.sum())


def main():
    data, scen, yrs, cached = load()
    val = {}
    # (1) levelization reproduces the workbook's cached outputs (combustion CO2, Mid-case, start 2025, 20 yr, 3%, end-use)
    lev = {g: levelize(data[(g, 'Mid-case')]['co2c'], yrs, start=2025) for g in ('ERCOT', 'PJM_East', 'PJM_West')}
    val['levelization'] = {g: dict(ours=lev[g], workbook=cached[g.replace('_', ' ')]) for g in lev}
    # (2) decomposition reproduces Cambium's precombustion CO2
    rec = {}
    for g in ('ERCOT', 'PJM_East', 'PJM_West'):
        for s in ('Mid-case', 'High Demand Growth'):
            gas, coal = decompose(data[(g, s)])
            pred = PRE_CO2['gas'] * gas + PRE_CO2['coal'] * coal
            rec[f'{g}|{s}'] = dict(years=yrs.tolist(), predicted=pred.round(2).tolist(), reported=data[(g, s)]['co2p'].round(2).tolist(),
                                   max_abs_rel_err_2027_2046=float(np.max(np.abs(pred[1:5] / data[(g, s)]['co2p'][1:5] - 1))))
    val['precombustion_co2_check'] = rec
    weights, miss, popsum = us_weights()
    val['us_weights'] = dict(weights=weights, counties_without_pop=miss, pop_total=popsum)

    rows = []
    geas = sorted({g for g, _ in data})
    for s in scen:
        for g in geas:
            d = data[(g, s)]
            for disc in (0.03, 0.0):
                rows.append(dict(gea=g, scenario=s, discount=disc,
                                 matched=to_busbar(levelize(matched_co2e(d), yrs, d=disc), d['dist_loss']),
                                 native=to_busbar(levelize(native_co2e(d), yrs, d=disc), d['dist_loss']),
                                 combustion_co2=to_busbar(levelize(d['co2c'], yrs, d=disc), d['dist_loss'])))
    df = pd.DataFrame(rows)
    # US: population-weighted GEA mean; PJM load-weighted variant uses population shares of East and West
    for (s, disc), grp in df.groupby(['scenario', 'discount']):
        gg = grp.set_index('gea')
        wus = pd.Series(weights).reindex(gg.index).fillna(0)
        rows.append(dict(gea='US (pop-weighted)', scenario=s, discount=disc,
                         **{c: float((gg[c] * wus).sum() / wus.sum()) for c in ('matched', 'native', 'combustion_co2')}))
        rows.append(dict(gea='US (equal-weighted)', scenario=s, discount=disc,
                         **{c: float(gg[c].mean()) for c in ('matched', 'native', 'combustion_co2')}))
        wp = pd.Series({k: weights[k] for k in ('PJM_East', 'PJM_West')})
        rows.append(dict(gea='PJM (pop-weighted E/W)', scenario=s, discount=disc,
                         **{c: float((gg.loc[wp.index, c] * wp).sum() / wp.sum()) for c in ('matched', 'native', 'combustion_co2')}))
    df = pd.DataFrame(rows)
    df.to_csv(OUT / 'cambium_matched.csv', index=False)
    json.dump(val, open(OUT / 'cambium_validation.json', 'w'), indent=1)

    print('levelization check:', {g: (round(v['ours'], 3), round(v['workbook'], 3)) for g, v in val['levelization'].items()})
    print('precombustion CO2 max rel err 2030-2045:', {k: round(v['max_abs_rel_err_2027_2046'], 4) for k, v in rec.items()})
    show = df[(df.discount == 0.03) & df.gea.isin(['ERCOT', 'PJM_East', 'PJM_West', 'PJM (pop-weighted E/W)', 'US (pop-weighted)'])]
    print(show.pivot_table(index='gea', columns='scenario', values='matched').round(0).T.to_string())
    print(df[(df.scenario == 'High Demand Growth') & df.gea.isin(['ERCOT', 'PJM_East', 'US (pop-weighted)'])].round(1).to_string())


if __name__ == '__main__':
    main()
