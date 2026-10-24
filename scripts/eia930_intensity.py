"""Annual production- and consumption-based CO2 intensity per BA from EIA-930 per-BA workbooks (stream: download, extract, delete).

Consumption intensity = sum(CO2 Emissions Consumed) / sum(Consumed Electricity) (EIA MRIO allocation of interchange).
Writes data/eia930_intensity.json. CO2 only (EIA estimates from fuel-specific factors); combustion basis.
"""
import json
import subprocess
import sys
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parents[1]
TMP = ROOT / 'data' / 'eia930'
TMP.mkdir(parents=True, exist_ok=True)
URL = 'https://www.eia.gov/electricity/gridmonitor/knownissues/xls/{}.xlsx'
BAS = sys.argv[1:] or ['EPE', 'PNM', 'WACM', 'PACE', 'TVA', 'SWPP', 'ERCO', 'PJM', 'MISO']
YEARS = [2023, 2024, 2025]
out_path = ROOT / 'data' / 'eia930_intensity.json'
out = json.load(open(out_path)) if out_path.exists() else {}

for ba in BAS:
    f = TMP / f'{ba}.xlsx'
    if not f.exists():
        subprocess.run(['curl', '-sL', '-A', 'Mozilla/5.0', '-o', str(f), URL.format(ba)], check=True)
    ws = openpyxl.load_workbook(f, read_only=True, data_only=True)['Published Daily Data']
    rows = ws.iter_rows(values_only=True)
    h = list(next(rows))
    ix = {k: h.index(k) for k in ['Local date', 'CO2 Emissions Generated', 'CO2 Emissions Consumed', 'Positive Generation',
                                  'Consumed Electricity', 'CO2 Emissions: COL', 'CO2 Emissions: NG', 'NG: COL', 'NG: NG',
                                  'CO2 Emissions Imported', 'CO2 Emissions Exported']}
    acc = {y: dict(gen_co2=0.0, cons_co2=0.0, pos_gen=0.0, cons_el=0.0, co2_col=0.0, co2_ng=0.0, gen_col=0.0, gen_ng=0.0,
                   co2_imp=0.0, co2_exp=0.0, days=0) for y in YEARS}
    for r in rows:
        d = r[ix['Local date']]
        if d is None or d.year not in acc:
            continue
        vals = [r[ix[k]] for k in ['CO2 Emissions Generated', 'CO2 Emissions Consumed', 'Positive Generation', 'Consumed Electricity']]
        if any(v is None for v in vals):
            continue
        a = acc[d.year]
        a['gen_co2'] += vals[0]; a['cons_co2'] += vals[1]; a['pos_gen'] += vals[2]; a['cons_el'] += vals[3]; a['days'] += 1
        for k, col in [('co2_col', 'CO2 Emissions: COL'), ('co2_ng', 'CO2 Emissions: NG'), ('gen_col', 'NG: COL'), ('gen_ng', 'NG: NG'),
                       ('co2_imp', 'CO2 Emissions Imported'), ('co2_exp', 'CO2 Emissions Exported')]:
            a[k] += r[ix[col]] or 0.0
    out[ba] = {str(y): dict(production_kg_mwh=1000 * a['gen_co2'] / a['pos_gen'] if a['pos_gen'] else None,
                            consumption_kg_mwh=1000 * a['cons_co2'] / a['cons_el'] if a['cons_el'] else None,
                            days=a['days'], consumed_TWh=a['cons_el'] / 1e6, generated_TWh=a['pos_gen'] / 1e6,
                            coal_share_gen_co2=a['co2_col'] / a['gen_co2'] if a['gen_co2'] else None,
                            gas_share_gen_co2=a['co2_ng'] / a['gen_co2'] if a['gen_co2'] else None,
                            coal_gen_TWh=a['gen_col'] / 1e6, gas_gen_TWh=a['gen_ng'] / 1e6,
                            imported_co2_Mt=a['co2_imp'] / 1e6, exported_co2_Mt=a['co2_exp'] / 1e6)
               for y, a in acc.items()}
    json.dump(out, open(out_path, 'w'), indent=1)
    f.unlink()
    print(ba, {y: (round(v['production_kg_mwh'] or 0, 1), round(v['consumption_kg_mwh'] or 0, 1), v['days']) for y, v in out[ba].items()}, flush=True)
