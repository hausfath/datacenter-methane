"""Hourly EIA-930 demand, net generation, interchange and generation by fuel for every BA, 2019 and 2023-2025 (stream: download, extract, delete).

Uses EIA's 'Adjusted' columns and keeps an imputed flag for demand. Time stamp = UTC hour ending.
Writes data/marginal/eia930_hourly.parquet.
"""
import subprocess
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data' / 'marginal'
TMP = OUT / 'tmp'
TMP.mkdir(parents=True, exist_ok=True)
URL = 'https://www.eia.gov/electricity/gridmonitor/sixMonthFiles/EIA930_BALANCE_{y}_{h}.csv'

def fuel_of(col):
    """Map an '(Adjusted)' net-generation-by-source column to a category. EIA renamed these columns in mid-2024."""
    c = col.split(' from ', 1)[1].replace('(Adjusted)', '').strip()
    if c.startswith('Solar'):
        return 'solar'
    if c.startswith('Wind'):
        return 'wind'
    if c.startswith('Hydropower'):
        return 'hydro'
    if 'Storage' in c:
        return 'storage'
    return {'Coal': 'coal', 'Natural Gas': 'gas', 'Nuclear': 'nuclear', 'All Petroleum Products': 'oil',
            'Other Fuel Sources': 'other', 'Unknown Fuel Sources': 'unknown'}.get(c, 'other')  # e.g. Geothermal


def complete(f, h):
    """True if the file ends with the last day of its half-year (EIA serves some files without Content-Length)."""
    if not f.exists() or f.stat().st_size < 10_000_000:
        return False
    with open(f, 'rb') as fh:
        fh.seek(-2000, 2)
        last = fh.read().decode('latin-1').strip().splitlines()[-1]
    return ('06/30/' if h == 'Jan_Jun' else '12/31/') in last.split(',')[1]


frames = []
for y in (2019, 2023, 2024, 2025):
    for h in ('Jan_Jun', 'Jul_Dec'):
        f = TMP / f'eia930_{y}_{h}.csv'
        url = URL.format(y=y, h=h)
        for _ in range(10):  # EIA's server often drops large transfers: refetch whole file until it is complete
            if complete(f, h):
                break
            f.unlink(missing_ok=True)
            subprocess.run(['curl', '-sL', '-A', 'Mozilla/5.0', '-o', str(f), url])
            time.sleep(5)
        else:
            raise RuntimeError(f'download failed: {f.name}')
        d = pd.read_csv(f, thousands=',', low_memory=False)
        cols = {'Balancing Authority': 'ba', 'UTC Time at End of Hour': 'utc', 'Demand (MW) (Adjusted)': 'demand',
                'Net Generation (MW) (Adjusted)': 'netgen', 'Total Interchange (MW) (Adjusted)': 'interchange',
                'Demand (MW) (Imputed)': 'demand_imputed', 'Region': 'region'}
        gen = [c for c in d.columns if c.startswith('Net Generation (MW) from') and c.endswith('(Adjusted)')]
        for c in gen:
            d[c] = pd.to_numeric(d[c], errors='coerce')
        cat = {c: fuel_of(c) for c in gen}
        byfuel = pd.DataFrame({f'gen_{k}': d[[c for c in gen if cat[c] == k]].sum(axis=1, min_count=1)
                               for k in sorted(set(cat.values()))})
        d = pd.concat([d[list(cols)].rename(columns=cols), byfuel], axis=1)
        for c in ('demand', 'netgen', 'interchange'):
            d[c] = pd.to_numeric(d[c], errors='coerce')
        d['utc'] = pd.to_datetime(d['utc'], format='%m/%d/%Y %I:%M:%S %p')
        d['demand_imputed'] = d['demand_imputed'].notna()
        frames.append(d)
        print(y, h, len(d), flush=True)

out = pd.concat(frames, ignore_index=True).drop_duplicates(['ba', 'utc'])
out.to_parquet(OUT / 'eia930_hourly.parquet', index=False)
print('saved', len(out), out.ba.nunique(), 'BAs')
for f in TMP.glob('eia930_*.csv'):
    f.unlink()
