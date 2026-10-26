# PLAN_marginal: average vs marginal grid emission factors (draft v1, 2026-10-26)

## Why
After the post went live, critics argued that the grid side should use a marginal emission factor, not the grid average. Zeke's position is that for new loads this large, a long-run (new-build) marginal rate is more appropriate than a short-run (operating) marginal rate. We will compute both, test whether any of them changes the post's conclusions, and make one shareable figure.

Scope (Zeke, 2026-10-26):
- Regions: ERCOT, PJM and US only (the main figure's grids). Hotspots are out of scope.
- Short-run rate: computed by us from hourly data and validated against a published product.
- Long-run definitions: Cambium LRMER, the recent build margin and the planned build margin. "All-gas new build" (the post's new NGCC, 455) was not selected. It stays in the table but not in the figure.

## Fixed from the main analysis (unchanged)
- Off-grid values at GWP100 and L = 2.3%: recip 736, simple-cycle turbine 705, SOFC 460, on-site CC 475 kg CO2e/MWh.
- Grid-side accounting follows `grid_avg()`:
  - combustion CO2 (plus CH4/N2O);
  - supply-chain CO2 of 9.3% of gas combustion CO2;
  - upstream CH4 at the matched L = 2.3%;
  - coal-mine CH4 of 0.199 kg/MMBtu coal;
  - all divided by (1 − 0.03) for T&D losses.
- Every marginal metric below is therefore built from **marginal heat input by fuel**, so that methane is treated identically on both sides.

## M1. Short-run marginal emission rate (SRMER), computed

**Data**
- EPA CAMPD Part 75 hourly unit-level emissions for 2024 and 2025: CO2 mass, heat input, gross load and unit fuel type.
  - Source: the quarterly national bulk files (about 1.8–2.0 GB each, 8 in total).
  - Each file is streamed: download, aggregate to region × fuel × hour, delete. Only about 2 GB is ever on disk.
- Unit → region mapping: plant ORIS code → balancing authority, from eGRID2023 PLNT BACODE. Plants not in eGRID2023 get the EIA-860 2024 BA code.
  - ERCOT = ERCO; PJM = PJM; US = lower-48 total.
- Load: EIA-930 hourly demand (six-month BALANCE files, about 45 MB each) for ERCO, PJM and the lower-48 sum. EIA's imputed/flagged values are kept as published, and we report the count of them.

**Specification (primary)**
- First differences, hour to hour: ΔY_t = β_b · ΔD_t + ε_t.
  - Y is in turn CO2 (kg), gas heat input, coal heat input and oil heat input (MMBtu).
  - D is BA demand (MWh).
  - b is a bin of season (4) × hour of day (24), giving 96 slopes per year.
- Flat-load SRMER = the equal-weight mean of β_b over all hours, since a data center draws roughly flat power.
- Demand, not fossil generation, is the regressor. This lets curtailed renewables, storage and imports absorb part of a demand change, as they do in reality.
- 90% CI from a moving-block bootstrap with 1-week blocks (1,000 draws).

**CO2e assembly**
- SRMER_CO2e = [β_CO2 + β_gasHI·53.06·0.093 + β_gasHI·upstream_CH4(L)·GWP + β_coalHI·0.199·GWP + combustion CH4/N2O (AP-42/40 CFR 98 Table C-2 by fuel)] / (1 − 0.03).

**Sensitivities**
1. Regressor = fossil generation from CEMS gross load (Siler-Evans 2012 / AVERT style). This sets an upper bound in which fossil is always marginal.
2. Pooled single β with no bins.
3. 2024 and 2025 separately.
4. Marginal T&D losses of 6% instead of 3%. Losses scale with I², so marginal losses are about twice average losses.
5. PJM imports: use the Eastern Interconnection's CEMS emissions against PJM demand.

**Validation (V-M1, pre-registered)**
- Target: EPA AVERT v4.3 (data year 2023) "Uniform EE" avoided CO2 rates, from `sources/marginal/MARGINAL_SOURCES.md` §1.1: Texas 587, Mid-Atlantic 618, national 648 kg CO2/MWh. These are combustion only.
- Method: we run M1 on 2023 data (CAMPD 2023 quarterly files, streamed the same way) and compare combustion CO2 only:
  - our ERCOT result vs AVERT Texas;
  - our PJM result vs AVERT Mid-Atlantic (an approximate footprint match, which we will state);
  - our lower-48 result vs AVERT national.
  - Both the primary (demand) regressor and sensitivity 1 (fossil load, closest to AVERT's basis) are compared.
- Pass: sensitivity 1 within ±10% for Texas and national. The Mid-Atlantic check is reported but is not pass/fail, because the footprints differ.
- If it fails: diagnose before any marginal number is used.
- Holland et al. 2022 (PNAS, 2019 marginal: Texas 492, East 638, US 591 kg CO2/MWh) is a directional check only, because its data years are older and its regions are interconnections.

## M2. Cambium long-run marginal emission rate (LRMER)
- Releases:
  - Cambium 2024 (already in `data/cambium/`), all scenarios: mid-case plus range.
  - A newer release, if one exists (research agent checking), and whether it reflects OBBBA.
- Metric: simple mean over 2027–2046 (20 years, matching the earlier context number), end-use basis, so no extra loss term is applied.
- Regions: ERCOT; PJM East and West, weighted by load (the earlier note used an unweighted mean; we will fix that and report both); national.
- Precombustion CH4 is rescaled to L = 2.3%. Cambium's own assumption (from its documentation, quoted in MARGINAL_SOURCES §1.5) is Alvarez 2018 with a 2.2% fugitive rate in 2022, declining linearly by 30% by 2030. We rescale by year: L·(1−Lc)/(Lc·(1−L)), where Lc is Cambium's rate. This raises the LRMER, which is conservative toward off-grid gas. The unadjusted value is also shown.
- Basis: Cambium values are per MWh of end-use demand, which includes distribution losses. Data centers connect at transmission, so we convert to busbar with Cambium's own 'Distribution Loss Rate' column and then apply our 3% T&D loss, as for the other grid metrics.
- US: Cambium gives no national value. We weight the GEA regions by 2024 state retail sales (EIA-861), allocated to GEA regions by county population share using the workbook's County Mapping tab. Equal weighting is a sensitivity.
- Caveats:
  - Cambium describes the LRMER as appropriate for interventions of "five years or longer" and for load anticipated by planners.
  - Cambium assumes a small increment of load, not GW-scale blocks.
  - Pre-OBBBA vintages assume IRA credits that have since been cut. Both of these bias the LRMER low, which counts in off-grid gas's favor here.

## M3. Recent build margin (UNFCCC CDM Tool 07 style)
- **Sample:** Tool 07's rule (version and wording to be quoted). Take units in the region ordered by commercial-operation date, newest first, and keep adding until they make up 20% of the region's annual generation (or the five most recent units, whichever is larger in generation). Also report a fixed window: units online 2021–2025.
- **Generation and fuel:**
  - Actual 2025 net generation and fuel use from EIA-923 (2024 if 2025 final data are not yet out).
  - For units that came online partway through the year, annualize with their region × technology capacity factor.
  - Batteries add no net generation and are excluded. Their charging losses are ignored, and this is noted.
- **CO2e:** each gas unit's actual heat rate (EIA-923 fuel ÷ generation) is passed through `em.intensity()` at L = 2.3%; coal (if any) gets coal-mine CH4. Total CO2e is divided by total generation, then by (1 − 0.03).
- **Combined margin:** CM = 0.5·OM + 0.5·BM, where OM is our M1 SRMER; shown in the table, not the figure.
  - **Open item, against Zeke's argument:** Verra's Oct 2024 draft says that for projects that *increase* grid consumption, Tool 07 sets wOM = 1, wBM = 0, i.e. operating margin only. We will try to verify this in Tool 07 v7.0 itself; the UNFCCC site blocked scripted access, so a browser is needed. If it is confirmed, the post-script must say so explicitly: the CDM convention for new consumption is short-run, and Tool 07 build margins were designed to credit new generation.
  - The build margin is still shown, because it answers "what is the grid adding", which is Zeke's framing.

## M4. Planned build margin
- **Units:** generators in EIA-860M (latest month) with planned operation in 2026–2028 in the region.
  - Primary: statuses U, V and TS (under construction or later).
  - Sensitivity: all planned, adding P, L, T and OT.
- **Generation:** region × technology capacity factors from the M3 units. For gas, use prime-mover-specific CFs and heat rates (CC, CT, IC); where a region has no recent unit of a type, use national recent averages.
- **Caveats:**
  - Planned renewables slip or are cancelled more often than gas.
  - Post-OBBBA credit phase-outs are partly reflected in the latest 860M.
  - This counts what is being built, not what is induced by data-center load (additionality).
  - Annual energy matching ignores timing: a flat load needs night-time supply.

## Blended lifetime metric (table only)
- Gagnon & O'Shaughnessy 2024 (NREL/TP-6A40-91580), MER = w·SRMER + (1 − w)·LRMER. Their worked example (a 3-year lag on a 20-year load) gives w = 0.15. They note that no research yet guides the choice of w.
  - We show w = 0.15 (central) and w = 0.25 (5-year lag).
  - The LRMER here is the Cambium value over the years after the lag.
  - The report was funded by Amazon; we disclose that when citing it.

## Outputs
- `scripts/marginal_campd.py`: streams CAMPD and writes `data/marginal/campd_hourly_{region}.parquet` (small).
- `scripts/marginal_srmer.py`: writes the regression, validation and bootstrap results to `results/marginal/srmer.csv` and `v_m1_avert.csv`.
- `scripts/marginal_build.py`: writes `results/marginal/build_margin.csv` (M3, M4).
- `scripts/marginal_compare.py`: runs M2, assembles everything and writes `results/marginal/grid_definitions.csv`, with each off-grid option's ratio to each definition.
- `scripts/make_marginal_figure.py` → `figures/marginal_vs_average.png`.
  - A dot plot with rows ERCOT, PJM and US, and x = kg CO2e/MWh.
  - Markers per row: grid average (as posted), SRMER with its 90% CI, Cambium LRMER (mid-case, with the scenario range as a bar), recent BM and planned BM.
  - The off-grid options are vertical reference lines labelled with their values.
  - Every displayed number is bound to the CSVs.
- METHODS.md gets a "Marginal emission factors" section; the README gets a short subsection.

## Pre-registered expectations (written before any computation)
- **SRMER, including upstream methane:**
  - ERCOT about 600–720 (gas-dominated);
  - PJM about 700–850 (coal still marginal at night);
  - US about 650–800.
  - So engines and turbines (705–736) would roughly tie the short-run marginal grid in ERCOT and the US and come in below it in PJM. SOFC and on-site CC would be clearly below the SRMER everywhere.
- **Long-run:**
  - The Cambium LRMER is far below everything (about 150–250).
  - The recent build margin (mostly solar and wind in ERCOT) is about 100–250.
  - The planned build margin is higher, at about 200–400, with more gas in PJM.
- **Interpretation:**
  - Under every long-run definition, all four off-grid options emit more than the grid; engines and turbines by more than 2×.
  - Under the short-run definition, the post's conclusion does not hold for fuel cells and CC, and is roughly a tie for engines and turbines.
  - The post's headline then depends on the horizon, and this should be stated plainly. Concede that the SR view is valid for the first few years of an unanticipated load, which is the argument that off-grid builders make (they are off-grid because interconnection is slow).

## Review
- Domain reviewer: power-systems marginal emissions.
- Methods reviewer: regression/statistics.
- Both review this plan before M1–M4 run. Deviations after the freeze go in §Change log.

## Change log
(empty)
