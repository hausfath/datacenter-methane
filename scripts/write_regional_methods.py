"""Append the regional section to METHODS.md from results/regional (all numbers computed here)."""
import json
from pathlib import Path

import pandas as pd

import regional as rg

ROOT = Path(__file__).resolve().parents[1]
d = pd.read_csv(ROOT / 'results/regional/regional_cases.csv')
e = rg.EIA
p = d[(d.pairing == 'matched') & (d.L_level == 'central') & (d.grid_basis == 'EIA-930 consumption 2025') & (d.gwp == 'AR6_100') & d.primary_case]
short = {'Recip engines (lean-burn)': 'Recip', 'Simple-cycle turbines': 'Simple cycle', 'Fuel cells (Bloom SOFC)': 'SOFC', 'Combined cycle (on site)': 'On-site CC'}
lines = ['| Region | Grid A / B (kg/MWh) | ' + ' | '.join(short.values()) + ' |', '|---|---|' + '---|' * 4]
for r, g in p.groupby('region', sort=False):
    g = g.set_index('case')
    lines.append(f"| {r} | {g.A.iloc[0]:.0f} / {g.B.iloc[0]:.0f} | " + ' | '.join(
        f"{g.loc[c, 'state']} ({g.loc[c, 'rel_A'] * 100:+.0f}% / {g.loc[c, 'rel_B'] * 100:+.0f}%)" for c in short) + ' |')
v = d[d.primary_case & d.case.isin(['Recip engines (lean-burn)', 'Simple-cycle turbines'])]
rob = {r: f"{(g.state == 'Worse').sum()}/{len(g)}" for r, g in v.groupby('region', sort=False)}
val = '; '.join(f"{k} {e[k]['2023']['production_kg_mwh']:.0f} vs {rg.EG[x]['co2_kg_mwh']:.0f}" for k, x in
                [('ERCO', 'ERCOT'), ('PJM', 'PJM'), ('MISO', 'ba_MISO'), ('SWPP', 'ba_SWPP'), ('TVA', 'ba_TVA'), ('PACE', 'ba_PACE'),
                 ('WACM', 'ba_WACM'), ('EPE', 'ba_EPE'), ('PNM', 'ba_PNM')])
yr = {k: rg.EIA_YEAR_OVERRIDE.get(k, rg.EIA_YEAR) for k in ['ERCO', 'SWPP', 'EPE', 'PJM', 'TVA', 'WACM', 'PACE']}
cons_header = ' | '.join(f'{k} ({y})' for k, y in yr.items())
cons_vals = ' | '.join(f"{e[k][y]['consumption_kg_mwh']:.0f}" for k, y in yr.items())

# West Texas SOFC reconciliation with the main analysis
c, C = 'Fuel cells (Bloom SOFC)', rg.CENTRAL
def rel(L, basis, cmm, fc):
    b = rg.btm(c, L, C['mf'], C['f'], 29.8)
    A = rg.grid_A('West Texas', L, C['mf'], C['f'], 29.8, C['loss'], cmm, fc, basis)
    return (b - A) / A * 100
steps = [rel(0.023, 'eGRID 2023 BA', 0.199, 0.0), rel(0.023, 'eGRID 2023 BA', 0.04, 0.02),
         rel(0.023, 'EIA-930 consumption 2025', 0.04, 0.02), rel(0.036, 'EIA-930 consumption 2025', 0.04, 0.02)]
ut = d[(d.region == 'Central Utah') & d.case.isin(['Recip engines (lean-burn)', 'Simple-cycle turbines']) & (d.grid_basis == 'EIA-930 consumption 2025')
       & (d.gwp == 'AR6_100') & (d.pairing == 'matched')].set_index(['case', 'L_level']).state
chey = p[p.region == 'Cheyenne'].set_index('case')

txt = f"""

# Regional sensitivity (PLAN_regional.md R2)
Scripts: `scripts/regional.py`, `scripts/eia930_intensity.py`, `scripts/make_regional_figures.py`, `scripts/write_regional_methods.py`. Figures: `figures/regional_heatmap.png`, `figures/regional_basin_ranges.png`.

## Setup
- **Regions.** Seven hotspot regions, taken from Cleanview project locations. Each is paired with its supplying basin's leak rate, matched on both sides. Leak rates are in `data/basin_leak_rates.json`, compiled in `sources/basins/BASINS.md`. Sources:
  - MacKay et al. 2026, ACP (MethaneAIR, 12 basins)
  - Varon et al. 2026, ES&T (TROPOMI)
  - Bridger 2024 inventory
  - AMI 2026
  - Sherwin et al. 2024, corrected SI
- **Grid A.** The EIA-930 consumption-based CO2 intensity of each balancing authority, which allocates interchange with an MRIO model (per-BA workbooks). The year is 2025, except SPP, where 2025 lacks December and 2024 is used. Added to it:
  - upstream gas CH4 and supply-chain CO2;
  - regional coal-mine CH4: surface/PRB/lignite mines 0.04 and underground mines 0.26 kg CH4/MMBtu (EPA GHGI 2023 Table 3-36; EIA ACR 2023 Table 1);
  - coal supply-chain CO2 at 2%;
  - the total is then divided by 0.97 (3% transmission loss).
- **Grid B.** A new H-class NGCC burning local gas.
- **States.** Four states with per-region MC tie bands (N = 20,000; L drawn triangular over the basin range).

## Grid data checks
EIA-930 2023 production intensity vs eGRID2023 BA CO2 (kg/MWh): {val}.
- Large ISOs agree within ±3%.
- Small and exporting BAs differ by up to about 80%. The two datasets attribute jointly owned and dynamically scheduled units differently. The eGRID BA and subregion bracket is reported for every cell.

Consumption intensity used, kg CO2/MWh:

| {cons_header} |
|{'---|' * len(yr)}
| {cons_vals} |

## Primary results
Matched central L, GWP100. Each cell gives the state, then % vs A / % vs B.

{chr(10).join(lines)}

## Reconciliation with the main analysis (West Texas fuel cells)
In the main analysis, SOFC was +9% vs ERCOT and "tied". In the regional run it is +24% and "above average". Each step's effect, applied in order:

| Step | SOFC vs ERCOT average |
|---|---|
| Main-analysis basis | {steps[0]:+.1f}% |
| Regional coal-mine CH4 and coal supply CO2 | {steps[1]:+.1f}% |
| EIA-930 2025 consumption instead of eGRID 2023 | {steps[2]:+.1f}% |
| Permian TX 3.6% instead of national 2.3%, matched | {steps[3]:+.1f}% |

ERCOT's lower 2025 intensity is the main driver. ERCOT's EIA-930 production intensity fell from {e['ERCO']['2023']['production_kg_mwh']:.0f} in 2023 to {e['ERCO']['2025']['production_kg_mwh']:.0f} in 2025.
A higher matched L also widens the gap, because BTM burns more gas per MWh than the grid. For a site in West Texas today, the regional view is the more current one. The main analysis keeps eGRID 2023 so that all three regions share one basis.

## Robustness
For recips and simple cycle, the table counts how many of the 22 variants per region come out "Worse". The 22 are 11 variants × 2 cases. The variants are:
- matched pairing at low, central and high L;
- local BTM gas vs national grid gas, at low, central and high L;
- energy-allocated L;
- EIA-930 2023 instead of 2025;
- eGRID BA;
- eGRID subregion;
- GWP20.

| Region | Variants "Worse" |
|---|---|
{chr(10).join(f'| {k} | {v} |' for k, v in rob.items())}

**Cheyenne** (WACM, a coal-heavy grid) is the one region where engines and turbines are not "Worse" at central assumptions.
- On DJ-basin gas, the case most favorable to on-site gas, recips are {chey.loc['Recip engines (lean-burn)', 'rel_A'] * 100:+.0f}% and simple cycle {chey.loc['Simple-cycle turbines', 'rel_A'] * 100:+.0f}% vs the 2025 average. Both are within the band, so they are tied with it.
- They are {chey.loc['Recip engines (lean-burn)', 'rel_B'] * 100:+.0f}% and {chey.loc['Simple-cycle turbines', 'rel_B'] * 100:+.0f}% vs a new grid gas plant.
- On Green River gas (5.2%) they are "Worse".
- The pre-registered "Between" wording applies.

**Central Utah's** "Worse" verdict depends on the Green River leak rate (5.2%), which is low confidence: MacKay covers 44% of production. Recips by L level: {', '.join(f'{lev} {ut.loc[("Recip engines (lean-burn)", lev)]}' for lev in ['low', 'central', 'high'])}. The heatmap title's "6 of 7" counts Utah.

**Fuel cells and on-site CC** tie a new grid NGCC in every region. Against regional averages they range from above (West Texas) to below (Cheyenne).

**El Paso.** EPE's grid burns more gas per MWh than SOFC or CC, so higher leak rates push those cells toward "below". As predicted, methane can cut either way there.

## Prediction vs outcome (PLAN_regional §8)
| Prediction | Outcome |
|---|---|
| Recips/SC "Worse" in West Texas, PJM, Memphis, Panhandle, El Paso | Correct |
| Cheyenne/Utah recips "Between" or "Worse" | Cheyenne "Between (above B)". Utah "Worse" at central L, "Between" at low L |
| CC/SOFC "Between" in Cheyenne/Utah | Cheyenne "Below A, tied B", a state missing from the §5 definitions (PLAN_regional §10). Utah "Tied" |
| Basin range dominates the Rockies bars | Correct. The Utah swing reaches 393 kg/MWh, but its 1.2% low end is a judgment call |

## Latent issues in the main analysis found by the regional review
These are flagged only. The main numbers are unchanged.
1. **Coal-mine CH4 factor.** The main analysis uses the national factor (0.199) everywhere. ERCOT's coal is surface lignite and PRB, at about 0.04. The national factor adds about 7 kg/MWh to ERCOT's grid (1.7% of A), which favors BTM.
2. **Coal supply-chain CO2.** It is missing on the grid side, about −3 kg/MWh in ERCOT and PJM, which favors the grid.

The two partly offset, and neither changes a main verdict.

## Caveats
- **Upstream scaling.** The consumption basis scales the grid's upstream terms by the BA's own fuel mix, which assumes imports have the same mix.
- **CO2 only.** EIA-930 reports CO2 only, so combustion CH4 and N2O are omitted on the grid side (<0.5%).
- **Basin rates.**
  - Denominators are not harmonized (gross, dry, covered or marketed gas).
  - Rockies values are low confidence.
  - Powder River and San Juan have no verified rate.
- **Cambium.** The 2024 LRMER for each site's GEA region is in `results/regional/regional_cases.csv` as pre-OBBBA context only.
"""
m = open(ROOT / 'METHODS.md').read()
i = m.find('\n\n# Regional sensitivity')
m = m if i < 0 else m[:i] + '\n'
open(ROOT / 'METHODS.md', 'w').write(m.rstrip('\n') + txt)
print(steps, rob)
