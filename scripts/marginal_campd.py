"""Hourly CEMS (EPA CAMPD Part 75) totals by balancing authority, fuel and unit class, in UTC (stream: download, aggregate, delete).

Writes data/marginal/campd/campd_{year}.parquet: one row per (BA, fuel, uclass, utc hour-ending) with CO2 (kg), heat input
(MMBtu), gross load (MWh) and the number of units reporting; plus campd_unmapped_{year}.json.

- Plant -> BA: eGRID2023 PLNT23 BACODE, then EIA-860M (Sep 2026) Operating and Retired sheets for plants not in eGRID2023.
- Fuel: by each unit-hour's CO2/heat-input ratio (kg/MMBtu): <60 gas, 60-85 oil, >=85 coal; unit primary fuel when the
  ratio is undefined. This handles multi-fuel labels such as "Coal, Natural Gas".
- CAMPD hours are local standard time, hour-beginning; converted per plant to UTC hour-ending (EIA-930 convention)
  from the plant's state (longitude cut for split states). Checked empirically by the lag test in marginal_srmer.py.
Part 75 has no reciprocating engines and few units under 25 MW.
Usage: EPA_API_KEY=... python3.13 marginal_campd.py YEAR [YEAR ...]  (free key from api.data.gov; DEMO_KEY is 10 requests/hour)
"""
import json
import os
import subprocess
import time
import sys
from pathlib import Path

import numpy as np
import openpyxl
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data' / 'marginal' / 'campd'
OUT.mkdir(parents=True, exist_ok=True)
TMP = ROOT / 'data' / 'marginal' / 'tmp'
TMP.mkdir(exist_ok=True)
URL = 'https://api.epa.gov/easey/bulk-files/emissions/hourly/quarter/emissions-hourly-{y}-q{q}.csv?API_KEY=' + os.environ.get('EPA_API_KEY', 'DEMO_KEY')
TON = 907.18474  # kg per short ton

# hours behind UTC, standard time
TZ = {**{s: 5 for s in 'CT DE DC FL GA IN KY ME MD MA MI NH NJ NY NC OH PA RI SC VT VA WV'.split()},
      **{s: 6 for s in 'AL AR IL IA KS LA MN MS MO NE ND OK SD TN TX WI'.split()},
      **{s: 7 for s in 'AZ CO ID MT NM UT WY'.split()},
      **{s: 8 for s in 'CA NV OR WA'.split()}, 'AK': 9, 'HI': 10, 'PR': 4}
# split states: (longitude cut, offset on the cut's far side, which side). Approximate; documented in METHODS.
SPLIT = {'FL': (-85.0, 6, 'west'), 'IN': (-86.8, 6, 'west'), 'KY': (-86.0, 6, 'west'), 'MI': (-87.5, 6, 'west'),
         'TN': (-85.5, 5, 'east'), 'TX': (-104.9, 7, 'west'), 'KS': (-101.5, 7, 'west'), 'NE': (-100.9, 7, 'west'),
         'ND': (-100.6, 7, 'west'), 'SD': (-100.6, 7, 'west'), 'ID': (-116.3, 8, 'west'), 'OR': (-117.3, 7, 'east')}


def offset(state, lon):
    off = TZ.get(state, 6)
    s = SPLIT.get(state)
    if s is None or lon is None or (isinstance(lon, float) and np.isnan(lon)):
        return off
    cut, alt, side = s
    return alt if (lon < cut if side == 'west' else lon > cut) else off


def plant_table():
    ws = openpyxl.load_workbook(ROOT / 'data/egrid/egrid2023_data_rev2.xlsx', read_only=True)['PLNT23']
    rows = ws.iter_rows(min_row=2, values_only=True)
    h = list(next(rows))
    ix = {k: h.index(k) for k in ['ORISPL', 'BACODE', 'PSTATABB', 'LAT', 'LON']}
    p = pd.DataFrame([{k: r[i] for k, i in ix.items()} for r in rows if r[ix['ORISPL']] is not None])
    p = p.rename(columns={'ORISPL': 'oris', 'BACODE': 'ba', 'PSTATABB': 'state'})
    p['oris'] = p['oris'].astype(int)
    p = p.drop_duplicates('oris').set_index('oris')
    m = pd.concat([pd.read_excel(TMP / 'eia860m_sep2026.xlsx', sheet_name=sh, header=2) for sh in ('Operating', 'Retired')])
    m = m[pd.to_numeric(m['Plant ID'], errors='coerce').notna()]
    m = m.groupby(m['Plant ID'].astype(int)).agg(ba=('Balancing Authority Code', 'first'), state=('Plant State', 'first'),
                                                 LAT=('Latitude', 'first'), LON=('Longitude', 'first'))
    p['ba'] = p['ba'].replace('', np.nan).fillna(m['ba'].reindex(p.index))
    p = pd.concat([p, m[~m.index.isin(p.index)]])
    p['LON'] = pd.to_numeric(p['LON'], errors='coerce')
    p['off'] = [offset(s, lon) for s, lon in zip(p['state'], p['LON'])]
    return p


def unit_class(u):
    u = (u or '').lower()
    if 'combined cycle' in u:
        return 'cc'
    if 'combustion turbine' in u:
        return 'ct'
    if 'internal combustion' in u:
        return 'ic'
    return 'boiler_other'


def primary_fuel(f):
    f = (f or '').lower()
    return 'coal' if f.startswith('coal') else 'gas' if 'natural gas' in f else 'oil' if 'oil' in f else 'other'


COLS = {'State': 'state_c', 'Facility ID': 'oris', 'Date': 'date', 'Hour': 'hour', 'Gross Load (MW)': 'gload',
        'CO2 Mass (short tons)': 'co2', 'Heat Input (mmBtu)': 'hi', 'Primary Fuel Type': 'fuel', 'Unit Type': 'utype'}


def process(path, plants, unmapped):
    parts = []
    for ch in pd.read_csv(path, usecols=list(COLS), chunksize=2_000_000, dtype={'Unit Type': str, 'Primary Fuel Type': str}):
        ch = ch.rename(columns=COLS)
        for c in ('gload', 'co2', 'hi'):
            ch[c] = ch[c].fillna(0.0)
        ch = ch[(ch.gload > 0) | (ch.hi > 0) | (ch.co2 > 0)].copy()
        if ch.empty:
            continue
        ch['co2'] *= TON
        ch['ba'] = ch['oris'].map(plants['ba'])
        miss = ch['ba'].isna()
        for o, g in ch[miss].groupby('oris'):
            u = unmapped.setdefault(str(o), dict(state=g['state_c'].iloc[0], co2_t=0.0))
            u['co2_t'] += float(g['co2'].sum() / 1000)
        ch['ba'] = ch['ba'].fillna('UNMAPPED_' + ch['state_c'])
        offs = ch['oris'].map(plants['off']).fillna(ch['state_c'].map(TZ)).fillna(6)
        ch['utc'] = pd.to_datetime(ch['date']) + pd.to_timedelta(ch['hour'] + offs + 1, unit='h')
        ratio = np.where(ch.hi > 0, ch.co2 / ch.hi.where(ch.hi > 0, 1), np.nan)
        ch['fuelc'] = np.select([ratio < 60, ratio < 85, ratio >= 85], ['gas', 'oil', 'coal'],
                                default=ch['fuel'].map(primary_fuel).fillna('other'))
        ch['uclass'] = ch['utype'].map(unit_class)
        ch['n'] = 1
        parts.append(ch.groupby(['ba', 'fuelc', 'uclass', 'utc'], observed=True)[['co2', 'hi', 'gload', 'n']].sum())
    return pd.concat(parts).groupby(level=[0, 1, 2, 3]).sum()


def download(f, url):
    """Resume dropped transfers. DEMO_KEY allows 10 requests/hour: on an OVER_RATE_LIMIT body, delete it and wait."""
    for i in range(40):
        r = subprocess.run(['curl', '-s', '--fail', '-C', '-', '--speed-limit', '20000', '--speed-time', '300', '-o', str(f), url])
        head = open(f, 'rb').read(200) if f.exists() else b''
        if r.returncode == 22 or not head.startswith(b'"State"'):   # HTTP error (e.g. OVER_RATE_LIMIT); --fail writes no body
            if head and not head.startswith(b'"State"'):
                f.unlink()
            print('rate limited; waiting 30 min', flush=True)
            time.sleep(1800)
            continue
        if r.returncode in (0, 33):
            return
        time.sleep(60 if 'DEMO_KEY' not in url else 400)
    raise RuntimeError(f'download failed: {f.name}')


def main(y):
    plants = plant_table()
    out_f, um_f = OUT / f'campd_{y}.parquet', OUT / f'campd_unmapped_{y}.json'
    have = pd.read_parquet(out_f) if out_f.exists() else None
    log = json.load(open(um_f)) if um_f.exists() else {}
    for q in (1, 2, 3, 4):
        key = f'{y}q{q}'
        if key in log:
            print('skip', key, flush=True)
            continue
        f = TMP / f'campd_{key}.csv'
        download(f, URL.format(y=y, q=q))
        unmapped = {}
        agg = process(f, plants, unmapped).reset_index()
        agg['quarter'] = key
        have = agg if have is None else pd.concat([have[have.quarter != key], agg], ignore_index=True)
        have.to_parquet(out_f, index=False)
        log[key] = unmapped
        json.dump(log, open(um_f, 'w'), indent=0)
        f.unlink()
        um = sum(v['co2_t'] for v in unmapped.values()) / 1e6
        print(key, f'rows {len(agg):,}  CO2 {agg.co2.sum() / 1e9:.1f} Mt  unmapped {um:.2f} Mt ({len(unmapped)} plants)', flush=True)


if __name__ == '__main__':
    for y in sys.argv[1:]:
        main(int(y))
