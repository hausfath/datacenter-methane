"""V2: consistency of Frost Methane's fleet numbers (Latitude Catalyst, 22 Oct 2026,
https://www.latitudemedia.com/news/catalyst-data-centers-looming-methane-surge/).

Stated: 50 GW; "7.5% of methane ends up in the atmosphere"; 380 Mt CO2e (100-yr) and 724 Mt (20-yr) "in the next 18 months";
"between 50 and 60% is CO2 and between 40 and 50% is methane"; GWPs "28 ... 84" (AR5).
"""
import json
from pathlib import Path

import numpy as np
from scipy.optimize import brentq

import emissions as em

OUT = Path(__file__).resolve().parents[1] / 'results'
CO2_PER_CH4 = 44.009 / 16.043
G100, G20 = 28.0, 84.0
R_OBS = 724 / 380


def ratio_produced_basis(f):
    """Pure-CH4 mass balance: fraction f of produced CH4 emitted, the rest burned."""
    return (CO2_PER_CH4 * (1 - f) + G20 * f) / (CO2_PER_CH4 * (1 - f) + G100 * f)


f_star = brentq(lambda f: ratio_produced_basis(f) - R_OBS, 0.01, 0.3)
f_range = [brentq(lambda f: (CO2_PER_CH4 * (1 - f) + G20 * f) / (CO2_PER_CH4 * (1 - f) + G100 * f) - hi / lo, 0.01, 0.3)
           for lo, hi in [(385, 720), (375, 728)]]
ch4_share_100 = G100 * f_star / (CO2_PER_CH4 * (1 - f_star) + G100 * f_star)

# kg CO2e per kg CH4 produced at GWP100, then CH4 produced and fuel energy
co2e_per_kg = CO2_PER_CH4 * (1 - f_star) + G100 * f_star
ch4_produced_kg = 380e9 / co2e_per_kg
ch4_burned_kg = ch4_produced_kg * (1 - f_star)          # includes slip denominator approx; slip is part of f
# pure CH4 HHV 55.5 MJ/kg -> MMBtu per kg
MMBTU_PER_KG = 55.5 / 1055.06
fuel_mmbtu = ch4_burned_kg * MMBTU_PER_KG
hours_18mo = 1.5 * 8766
cf_hr_18mo = fuel_mmbtu / (50e3 * hours_18mo)           # MMBtu/MWh x CF if 18 months of operation
cf_hr_annual = fuel_mmbtu / (50e3 * 8766)                # if 380 Mt is an annual rate

# Split of the 7.5%: slip share of produced CH4 for a fleet with recip share s and recip slip x (fraction of CH4 in),
# turbines ~0.02%. Residual = upstream + midstream + facility.
recip_share = np.linspace(0, 1, 11)
slip_frac = np.array([0.015, 0.02, 0.028, 0.035])
surface = {}
for x in slip_frac:
    fleet_slip = recip_share * x + (1 - recip_share) * 0.0002
    # slip is a fraction of CH4 reaching the engine; on the produced basis multiply by (1 - upstream share)
    resid = [brentq(lambda u: u + (1 - u) * s - f_star, 0, f_star) for s in fleet_slip]
    surface[f'slip_{x:.3f}'] = [round(r * 100, 2) for r in resid]

res = dict(
    f_star_pct=round(f_star * 100, 3), f_range_pct=[round(v * 100, 2) for v in f_range],
    ratio_model=round(ratio_produced_basis(0.075), 4), ratio_obs=round(R_OBS, 4),
    ch4_share_gwp100_pct=round(ch4_share_100 * 100, 1),
    cf_x_hr_if_18_months=round(cf_hr_18mo, 2), cf_x_hr_if_annual=round(cf_hr_annual, 2),
    implied_annual_rate_if_18_months_Mt=round(380 / 1.5, 0),
    residual_upstream_plus_facility_pct_by_recip_share=dict(recip_share=[round(r, 1) for r in recip_share], **surface),
    note='Residual = share of produced CH4 lost before the engine implied once fleet slip is removed; Irzak states 4% '
         'wellhead + gathering for the Permian. Cleanview identified equipment is ~34% recips, ~46% simple-cycle turbines, ~14% fuel cells (data/planned_technology_shares.json).')
print(json.dumps(res, indent=1))
json.dump(res, open(OUT / 'v2_frost.json', 'w'), indent=1)
