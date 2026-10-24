"""V3: FaIR pulse metrics vs AR6. 100 Mt CH4 and 100 Mt CO2 pulses in 2030 on SSP2-4.5; A-A zero test.

Compares the 100-yr integrated-ERF ratio (GWP-like) and the 100-yr temperature ratio (GTP-like) with AR6
non-fossil CH4 values (FaIR has no CH4 oxidation).
"""
import json
from pathlib import Path

import numpy as np

import fair_runs as fr

OUT = Path(__file__).resolve().parents[1] / 'results'
OUT.mkdir(exist_ok=True)
tp = fr.timepoints()
i0 = int(np.where(tp == 2030.5)[0][0])
SIZE = 100.0   # Mt

base_T, base_F = fr.run('ssp245')
aa_T, _ = fr.run('ssp245')
zero = float(np.abs(aa_T - base_T).max())

ch4 = np.zeros(len(tp)); ch4[i0] = SIZE
co2 = np.zeros(len(tp)); co2[i0] = SIZE / 1000
T_ch4, F_ch4 = fr.run('ssp245', ch4_mt=ch4)
T_co2, F_co2 = fr.run('ssp245', co2_gt=co2)
# half-size CH4 pulse for linearity
T_ch4h, _ = fr.run('ssp245', ch4_mt=ch4 / 2)

tb = np.arange(fr.START, fr.END + 1)
j0 = int(np.where(tb == 2030)[0][0])
H = 100
dF_ch4 = (F_ch4 - base_F)[j0:j0 + H + 1].sum(axis=0)
dF_co2 = (F_co2 - base_F)[j0:j0 + H + 1].sum(axis=0)
gwp = dF_ch4 / dF_co2
dT_ch4 = (T_ch4 - base_T)[j0 + H]
dT_co2 = (T_co2 - base_T)[j0 + H]
gtp = dT_ch4 / dT_co2
lin = ((T_ch4h - base_T)[j0 + 20] / (T_ch4 - base_T)[j0 + 20])

q = lambda a: [float(x) for x in np.percentile(a, [5, 50, 95])]
agwp_co2 = dF_co2 / (SIZE * 1e9)     # W m-2 yr per kg
agwp_ch4 = dF_ch4 / (SIZE * 1e9)
res = dict(agwp100_co2_per_kg=q(agwp_co2), agwp100_ch4_per_kg=q(agwp_ch4),
           ar6_agwp_ref='AR6 7.SM: AGWP100 CO2 8.95e-14 W m-2 yr kg-1 [verify]; CH4 non-fossil = 27.0 x that = 2.42e-12',
           aa_zero_max_abs=zero, gwp100_like=q(gwp), gtp100_like=q(gtp), linearity_half_over_full_yr20=q(lin),
           ar6_ref='AR6 WG1 Table 7.15 CH4 non-fossil: GWP100 27.0 +/- 11, GTP100 4.7 +/- 2.8 [verify]')
print(json.dumps(res, indent=1))
json.dump(res, open(OUT / 'v3_fair_metrics.json', 'w'), indent=1)
