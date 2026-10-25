"""Recip slip sensitivity: what if fleet-average engine slip is well above the 40 CFR 98 W-7 factor?

Irzak (Catalyst, 2026-10-22) cites measurements "up to 12%" of CH4 slipping at partial load. This brackets that
against the main-analysis references at the primary matched leak rate. Writes results/slip_sensitivity.csv.
"""
from pathlib import Path

import pandas as pd

import emissions as em
from cases import L_PRIMARY, btm, grid_avg, grid_ngcc, tot

OUT = Path(__file__).resolve().parent.parent / 'results' / 'slip_sensitivity.csv'
RECIP = 'Recip engines (lean-burn)'
SLIP_W7 = 0.522                     # kg CH4/MMBtu, 40 CFR 98 Table W-7, 4-stroke lean burn


def main():
    c = em.ch4_content()            # kg CH4/MMBtu delivered
    refs = {r: tot(grid_avg(r, L_PRIMARY)) for r in ('ERCOT', 'PJM', 'US')}
    refs['New grid NGCC'] = tot(grid_ngcc(L_PRIMARY))
    rows = []
    for label, share in [('W-7 (central)', SLIP_W7 / c), ('4%', 0.04), ('6%', 0.06), ('12%', 0.12)]:
        e = tot(btm(RECIP, L_PRIMARY, slip=share * c))
        rows.append(dict(slip_label=label, slip_share=share, recip_kgCO2e_MWh=e,
                         **{f'ratio_vs_{k}': e / v for k, v in refs.items()}))
    df = pd.DataFrame(rows)
    df.to_csv(OUT, index=False, float_format='%.4f')
    print(df.round(3).to_string(index=False))
    print({k: round(v, 1) for k, v in refs.items()})


if __name__ == '__main__':
    main()
