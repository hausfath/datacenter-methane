# PLAN_marginal: average vs marginal grid emission factors (v2, FROZEN 2026-10-26 after domain + methods review)

v1 as reviewed: `reviews/PLAN_marginal_v1_as_reviewed.md`. Reviews: `reviews/marginal_domain_review.md`, `reviews/marginal_methods_review.md`. How each must-fix was handled is listed in §Review response. Deviations after this freeze go in §Change log.

## Why
After the post went live, critics argued that the grid side should use a marginal emission factor, not the grid average. Zeke's position is that for loads this large, a long-run (new-build) marginal rate is more appropriate than a short-run (operating) one. We compute both, test whether either changes the post's conclusions, and make one shareable figure.

Scope (Zeke, 2026-10-26):
- Regions: ERCOT, PJM and the US. Hotspots are out of scope.
- The short-run rate is computed by us from hourly data and validated against a published number.
- Long-run comparators: Cambium LRMER, recent additions, planned additions and, restored after review at Zeke's request, the all-gas new build (new grid NGCC, 455).
- Framing (Zeke): report both horizons and state the result plainly, including any short-run tie or reversal.

## Rule for defensible-either-way choices
The claim being critiqued is the post's: that the grid is cleaner than off-grid engines and turbines. Where a choice is defensible either way, the primary takes the option that makes the grid look **dirtier**, and the alternative runs as a sensitivity. Departures from this rule are named.

## Fixed from the main analysis (unchanged)
- Off-grid values at GWP100 and L = 2.3%: recip 736, simple-cycle turbine 705, SOFC 460, on-site CC 475 kg CO2e/MWh.
- Grid accounting follows `grid_avg()`:
  - combustion CO2 (plus CH4/N2O);
  - supply-chain CO2 at 9.3% of gas combustion CO2;
  - upstream CH4 at L = 2.3% via `em.upstream_ch4`;
  - coal-mine CH4 at 0.199 kg/MMBtu coal (the posted national value, which is higher than regional surface-mine values; regional CMM is a sensitivity);
  - divided by (1 − loss).
- Every marginal metric is built from **marginal heat input by fuel**, so methane is treated identically on both sides.

## M1. Short-run marginal emission rate (SRMER)

**Data**
- EPA CAMPD Part 75 hourly unit data for 2019 (validation), 2023 (AVERT check), 2024 and 2025.
  - Quarterly national bulk files are streamed (download → aggregate → delete).
  - Aggregated to BA × fuel (gas/coal/oil/other) × unit class (CC/CT/IC/boiler) × UTC hour (`scripts/marginal_campd.py`).
  - CAMPD hours are taken as local standard time, hour-beginning. Each plant's UTC offset comes from its state, with longitude cuts for split states. This is verified empirically by D1(a).
- Plant → BA: eGRID2023 BACODE, with EIA-860M (Sep 2026) as the fallback for newer plants. Unmapped CO2 is reported.
- Demand: EIA-930 hourly "Demand (Adjusted)", stamped UTC hour-ending (`scripts/marginal_eia930.py`).
- Interconnections, by EIA-930 region of the BA: Texas = TEX; Western = CAL + NW + SW; Eastern = all others.

**Primary specification (Holland et al. 2022, which we reproduce first)**
- Levels: Y_t = β·D_t + month-of-sample FE + hour-of-day FE + ε_t, with Newey–West SEs at 48 lags.
- Y_t is, in turn, CO2e on the project basis (one dependent variable, per methods SF6), CO2, gas heat input, coal heat input and oil heat input.
  - CO2e_t = CO2_t + gasHI_t·(53.06·0.093 + upstream_ch4(L)·GWP) + coalHI_t·0.199·GWP + combustion CH4/N2O (Table C-2 by fuel).
- System boundary:
  - **ERCOT:** ERCOT CEMS on ERCO demand.
  - **PJM:** Eastern Interconnection CEMS on PJM demand *and* rest-of-Eastern demand as joint regressors (the Graff Zivin et al. 2014 spillover design). The PJM coefficient is the headline.
  - **US:** the Holland-style estimate for each interconnection, load-weighted.
- Headline year: 2025.
- Losses: **marginal T&D losses of 6%** (Cambium's convention for short-run metrics), so SRMER_delivered = β / (1 − 0.06).
- Cleaning:
  - drop hours where demand is imputed or missing;
  - drop hours with |D − rolling 24 h median| > 5 × MAD;
  - drop hours where the CEMS unit count in the region departs from the day's mode by more than 5%;
  - report all counts.

**Specification envelope (pre-registered; the figure's bar is its range)**
- R1 estimator: levels + FE (primary) | first differences with season × hour bins and bin intercepts | 24-hour differences | daily totals with month-of-sample and day-of-week FE (nets storage and unit commitment within the day).
- R2 renewables: none (primary, as in Holland) | wind and solar output as controls.
- R3 boundary: as above (primary) | PJM own CEMS on PJM demand | a single pooled lower-48 regression.
- R4 regressor: demand (primary) | fossil load (CEMS gross load; "fossil-always-marginal", the AVERT/Siler-Evans basis).
- Also reported, outside the envelope:
  - years (2024, pooled 2024–25);
  - 3% average losses;
  - regional CMM;
  - bootstrap CI (weekly moving blocks, 2,000 draws, seed 20261026).

**Diagnostics (D1, must pass before any SRMER is used)**
- **(a) Time alignment.** For ERCOT and PJM, the cross-correlation of first-differenced CEMS CO2 and demand peaks at lag 0 in at least 10 of 12 months.
- **(b) Holland reproduction (V-M1a).** Primary spec on 2019 data:
  - Texas within ±5% or 2 Newey–West SEs (whichever is wider) of 1.085 lb/kWh (492 kg/MWh) CO2;
  - Eastern Interconnection, same test against 638.
  - Holland used FERC 714 load, and we use EIA-930.
  - If the levels spec fails and another spec passes, the passing spec becomes primary. That choice is made on validation, not on the 2025 answer.
- **(c) AVERT v4.3 2023 check.** Compare at generation level, using AVERT's own loss factors:
  - Texas 560, Mid-Atlantic 574, national about 600 kg CO2/MWh (domain review §1.3).
  - The R4 fossil-load variant must fall within ±10% for Texas and Mid-Atlantic (pass/fail).
  - The demand primary is expected 5–15% below (reported, not pass/fail).
- **(d) Fuel closure.** β_CO2 is within 3% of 53.06·β_gasHI + β_coal·EF + β_oil·EF, using the CAMPD-implied CO2/heat-input ratios.
- **(e) Plausibility.**
  - Fossil share of marginal demand: 0.6–1.05.
  - Implied marginal gas heat rate: 6.5–11 MMBtu/MWh.
  - CEMS CO2 coverage of EIA-930 production CO2 is reported per region. If it is below 95%, the R7-style scaled variant is reported.

**Known limits (stated, not fixed)**
- CEMS misses most units under 25 MW, including small recips and peakers.
- Substitute data are not separated, since the aggregation kept no measure indicators.
- ERCOT flexible loads (crypto) respond to prices.
- This is a linear approximation for GW-scale increments.

## M2. Cambium 2024 LRMER (long-run)
- **Matched reconstruction (both reviews' must-fix).** Back out marginal gas and coal heat input per year and region from Cambium's combustion CO2 and CH4. Cambium's factors: CO2 53.06·G + 95.52·C; CH4 1.0·G + 11.0·C g/MMBtu. Then re-apply the project's accounting:
  - upstream CH4 at L = 2.3%;
  - f = 0.093;
  - CMM 0.199.
  - Validation: the reconstruction must reproduce Cambium's own precombustion CO2 to within 3% for ERCOT and PJM_East.
- **Scenario and window.** Primary is High Demand Growth, levelized 2027–2046 at Cambium's default 3% discount rate. Variants: the range across all 8 scenarios, a simple mean (0%), and the native (unmatched) values.
  - We verify that our levelization reproduces the workbook's own levelized ERCOT value.
- **Regions:**
  - PJM = PJM_East, where the data-center load is (Loudoun → PJM_East). An East/West load-weighted mean is the variant.
  - US = GEA regions weighted by county population (Census 2020) via the workbook's County Mapping tab. Equal weighting is the variant.
- **Basis.** End-use → busbar using Cambium's Distribution Loss Rate, then /(1 − 0.03) average losses, Cambium's convention for long-run metrics.
- **Bias statement.** Cambium 2024 has IRA credits never phasing out in all scenarios, and includes the 2024 EPA §111 power-plant rule (repeal status to be checked in the Federal Register before we cite it). Both push the LRMER low, by an unknown amount. A single GW campus is within Cambium's perturbation size; the 50–90 GW aggregate is not.

## M3. Recent additions (average emission rate of recently built capacity, labelled as such, not "new-build marginal")
- **Sample:** the Tool 07 build-margin rule as quoted in the Verra draft (MARGINAL_SOURCES §2.4). Take the most recent units that together supply ≥20% of 2025 regional generation, or the 5 most recent units if those supply more. Only units with a full year of 2025 data are included (online by Dec 2024).
- **Data:** EIA-860M (Sep 2026) for operating dates and BA; EIA-923 2025 Final for generation and fuel at plant × prime-mover level. CC turbine and steam parts are combined. Plants where new and old units share a prime mover are excluded and counted.
- **CO2e:** gas units through `em.intensity()` with their own heat rate. Recip units get W-7 slip, the same as off-grid recips. Total CO2e is divided by total generation, then /(1 − 0.03).
- **Variant:** a fixed window of units online 2020–2024.
- **Batteries:** excluded (no net generation); their charging losses are ignored, and this is stated.

## M4. Planned additions (average emission rate of the 2026–2030 pipeline)
- EIA-860M (Sep 2026) planned units with operation in 2026–2030.
  - Primary: under construction or later (U, V, TS).
  - Variant: all planned (adding P, L, T, OT).
- Generation from region × technology capacity factors observed in M3. Gas units by prime mover (CC, CT, IC) with M3 heat rates, falling back to national recent-unit averages.
- Caveats: renewables slip and get cancelled more than gas; this is an average of additions, not the additions caused by the load (additionality); annual energy matching ignores night-time supply for a flat load (no hourly-matched version is computed).

## M5. All-gas new build (restored)
New grid H-class NGCC: 455 kg CO2e/MWh at L = 2.3% (`grid_ngcc()`), with 3% losses as posted. This is the "utility builds gas for the load" bound. The LPSC order for Entergy/Meta (3 CC + up to 1.5 GW solar) is cited as an example of a real procurement that falls between M4 and M5. No stylized procurement row is computed: there is too little documentation to set its energy mix.

## Blend (in the figure)
- MER = w·SRMER + (1 − w)·LRMER, from Gagnon & O'Shaughnessy 2024 (Amazon-funded; disclosed).
- w = 0.25 central (a 5-year lag on a 20-year load), range 0.15–0.35 (3- to 7-year lags).
- Inputs: the primary SRMER and the M2 primary LRMER.

## Outputs
- `scripts/marginal_campd.py` → `data/marginal/campd_hourly_ba.parquet`
- `scripts/marginal_eia930.py` → `data/marginal/eia930_hourly.parquet`
- `scripts/marginal_srmer.py` → `results/marginal/srmer_specs.csv`, `diagnostics.json`
- `scripts/marginal_cambium.py` → `results/marginal/cambium_matched.csv`
- `scripts/marginal_build.py` → `results/marginal/build_margins.csv`
- `scripts/marginal_compare.py` → `results/marginal/grid_definitions.csv` (every metric × region, ratio and verdict for each off-grid option)
- `scripts/make_marginal_figure.py` → `figures/marginal_vs_average.png`
  - Three small-multiple panels (ERCOT, PJM, US).
  - Metric rows ordered by horizon: average (as posted), short-run marginal, blend, Cambium long-run, planned additions, recent additions, all-gas new build.
  - Off-grid options shown as two shaded vertical bands (engines/turbines 705–736; fuel cells/CC 460–475).
  - Colored by metric family. Bars: the SRMER envelope with the bootstrap CI as an inner tick, the Cambium scenario range and the blend's w range.
  - All text bound to the CSVs.
- METHODS.md section and README subsection.

## Decision rule (pre-registered)
- For each off-grid option × region × metric, the tie band = max(5%, half-width of the metric's plotted range relative to its central value).
  - "Worse" if off-grid > grid × (1 + band).
  - "Better" if off-grid < grid × (1 − band).
  - "Tie" otherwise.
- **Post-script wording template (Zeke: report both horizons, state it):**
  - "On today's short-run margin, off-grid engines and turbines are [worse than / roughly level with / cleaner than] the grid in [regions]. Fuel cells and on-site combined cycle are [..]. On a long-run basis, they are [..]. That holds for the blend NREL recommends for long-lived loads, for Cambium's long-run rate, for the average of planned additions, and even against a new gas plant on the grid."
  - Concessions:
    - the short-run view is right for the first years of a load the grid can't yet serve;
    - Cambium is pre-OBBBA and so too clean;
    - if the alternative to off-grid gas in years 1–3 is *no* data center rather than grid power, the comparison is moot for those years.

## Pre-registered expectations (v2; revised after review arithmetic but before any 2024–25 computation)
- **SRMER primary** (levels, demand, 6% losses), kg CO2e/MWh delivered:
  - ERCOT about 650–780;
  - PJM about 680–800;
  - US about 700–820.
  - The fossil-load variant is about 10% higher.
  - The domain review's AVERT-based arithmetic gives about 725–770 at 3% losses.
  - So engines and turbines (705–736) most likely come out **tied** with the short-run margin, possibly below it in one or more regions. Fuel cells and CC come out clearly below it (cleaner than the short-run marginal grid).
- **Long-run.** These values were already known, so they are not predictions:
  - Cambium matched HDG: ERCOT about 166, PJM_East about 278.
- **Predictions for the rest:**
  - recent additions about 100–300 (ERCOT, solar/wind-heavy) and 300–500 (PJM, which may reach back to the CC wave);
  - planned additions about 150–400;
  - blend about 300–400.
- **Interpretation pre-committed:**
  - engines and turbines exceed every long-run comparator, including the all-gas new build;
  - SOFC and CC tie the all-gas new build and exceed the renewable-heavy comparators;
  - on the short-run margin, the post's conclusion does not hold for SOFC and CC, and is roughly a tie for engines and turbines.

## Review response (v1 → v2)
- **Both reviews: Cambium methane rescaling.** Replaced with a matched reconstruction from heat input (M2).
- **Domain 1.1 / Methods SF1: first differences.** Levels + FE (Holland) is now primary; the others are in the envelope.
- **Domain 1.2 / Methods MF5: validation.** Added the Holland 2019 reproduction (D1b); AVERT moved to generation level with loss factors (D1c).
- **Methods MF2: renewables controls.** Kept as an envelope variant (R2), not primary. Holland, which we must reproduce, has none, and the controls also remove legitimate curtailment response.
- **Methods MF3: time alignment.** Per-plant UTC conversion and lag test D1(a).
- **Both: PJM imports.** Joint regressors are now primary for PJM; the US is load-weighted across interconnections.
- **Both: pre-registered decision and wording.** Added above.
- **Domain: restore new NGCC.** Done (M5), on Zeke's approval.
- **Should-fix items adopted:**
  - marginal losses for SR;
  - High Demand Growth, PJM_East and the 3% discount as Cambium primaries;
  - blend in the figure with w = 0.25;
  - build margins relabelled and restricted to full-year units;
  - figure redesigned as small multiples with bands.
- **Not adopted (reasons):**
  - Stylized utility-procurement row: too little documentation (cited in text instead).
  - Hourly-matched build margin: not computed; caveat stated.
  - Substitute-data variant: the aggregation has no indicators; caveat stated.
  - Regional CMM as primary: kept 0.199 for continuity with the posted figure and because it is conservative toward the critique; regional CMM is a sensitivity.
  - Data-center-weighted US: the US is load-weighted only, and PJM_East is shown for PJM.
  - Tool 07 OM-only weighting for consumption: one sentence, flagged as from a Verra draft, unverified in TOOL07 itself.

## Change log
- **2026-10-26, D1a.** On the earlier 2023 CEMS aggregate (combustion CO2 only, before any CO2e or 2024–25 result was seen), the pre-registered lag test peaks at +1 h for ERCOT in June–October and at −1 h in November–December. PJM peaks at 0 all year.
  - Comparing CEMS gross load with EIA-930 fossil generation (the same physical quantity) shows ERCOT aligned at lag 0 in every month. Of 18 large BAs checked, every one except PJM aligns at 0, with correlations of 0.95–0.99.
  - So ERCOT's summer offset is physical: solar shifts the net-load ramp relative to demand. It is not a timestamp error.
  - Added a timestamp check: CEMS gross load vs EIA-930 demand, excluding June–August. The pre-registered test is still reported.
- **2026-10-26, PJM.** PJM's EIA-930 fuel-mix columns are offset by 1 h relative to CEMS in 2019, 2023 and 2024, but not in 2025. PJM demand is aligned with CEMS at lag 0 (correlation 0.92–0.93 in every season).
  - The primary spec uses demand and is unaffected.
  - The PJM wind/solar controls (R2) are shifted by the detected lag, and the lag is recorded in diagnostics.json.
- **2026-10-26, cleaning.** The CEMS "unit count departs from the day's mode" rule was replaced by a 5×MAD screen on CEMS CO2 against its rolling 24-hour median. The count of operating units changes with dispatch, so the original rule would have removed real responses.
- **2026-10-26, CEMS fuel and mapping.**
  - Fuel is classified per unit-hour by the CO2/heat-input ratio (multi-fuel labels such as "Coal, Natural Gas").
  - EIA-860M is the plant→BA fallback.
  - Remaining unmapped plants are assigned by EIA-860M lookup: TX→ERCO, LA→MISO, MD/OH→PJM.
  - Part 75 data contain no reciprocating engines, so CEMS slip assignment for IC units never triggers.
- **2026-10-26, Cambium US weights.** County population is the Census 2024 estimate, not Census 2020.
- **2026-10-26, data gaps (Zeke: "validate on what we have").** EPA's DEMO_KEY hit its rate limit.
  - The Holland reproduction (D1b) uses January–September 2019, not the full year.
  - The AVERT check (D1c) uses the earlier 2023 aggregate. That aggregate classifies fuel by the primary-fuel label, which does not affect CO2 or gross load.
  - 2024 is not computed.
  - D1b passed: Texas 484 vs 492, Eastern 614 vs 638.
  - D1c fossil-load passed: ERCOT −7.7%, PJM +8.5%.
  - D1c demand spec vs AVERT came in at ERCOT −23.5%, PJM −6.7% and US −18.8%. Two of the three are outside the pre-registered 5–15%-below expectation.
- **2026-10-26, D1e failure and the rule adopted (written before regenerating any output).** The pre-registered 2025 primary (levels, demand, no renewables controls, joint PJM boundary) fails D1e in two regions:
  - ERCOT fossil share is 0.55. Every uncontrolled demand spec there gives 0.33–0.57, except the daily spec at 0.71. Every spec with wind and solar controls passes (0.77–0.96). This is the solar/demand weather confounding that the methods review predicted (MF2). The 2019 Holland pass does not carry over, because ERCOT had little solar in 2019.
  - PJM: the joint Graff Zivin boundary gives a fossil share of 1.24 (1.06 with controls), which is not physical. PJM's own boundary passes (0.93).
  - **Rule:**
    - (1) Adopt MF2 uniformly: wind and solar controls become the primary R2 setting in all three regions. The estimator stays levels and the regressor stays demand, as pre-registered.
    - (2) If the primary boundary still fails D1e, fall back to the alternative boundary. That applies to PJM, where the own boundary is used. Own-CEMS understates PJM's response, because part of a demand change is met by changing exports, so this choice biases the grid number low, in off-grid gas's disfavor.
    - (3) The figure's envelope uses only D1e-passing specifications, including the fossil-load (R4) variants.
    - (4) The bootstrap CI is computed on the new primary spec.
  - The uncontrolled values and the median of passing specs are reported alongside.
  - ERCOT's result came in below the pre-registered 650–780 expectation. Law-firm alerts (Beveridge & Diamond; Jackson Walker) report that EPA finalized a partial repeal of the 2024 rule on 2026-09-17, effective 2026-11-16, and proposed a full repeal. Not checked in the Federal Register.
- **2026-10-26, verdict rule (post hoc, after the first verdicts.csv).** The band is now max(5%, the main analysis's Monte Carlo tie band for that option and region, the metric's half-range). The pre-registered rule omitted the MC term.
  - Effect: SOFC against the 2023 grid average flips from "worse" to "tie" in ERCOT (1.09×) and the US (1.06×), which reproduces the post's own verdicts.
  - No engine or turbine cell changes, and no short-run or long-run cell changes.
  - Reason: the MC band carries the off-grid side's own uncertainty, which does not depend on how the grid is counted.
- **2026-10-26, figure subtitle (post hoc).** Per-region short-run verdicts were replaced by ratio ranges (engines and turbines 0.9–1.4×; fuel cells and CC 0.6–0.9×).
  - Reason: ERCOT's short-run verdict flips between the primary levels spec (538 → engines 1.31–1.37×, "worse") and the daily-totals spec, which nets battery charging (663 → 1.06–1.11×, "tie").
  - Neither is clearly right, so the figure states the ratio range, and METHODS gives both.
- **2026-10-26, D1d fuel closure.** The first run missed for PJM (−3.7% vs ±3%). Cause: each dependent variable had its own 5×MAD outlier screen, so the fuel equations ran on slightly different hours from the CO2 equation (methods review SF6). All dependent variables now share the CO2e-screened sample.
  - Closure is now +1.2% / −0.8% / 0.0% (pass).
  - Headline CO2e values are unchanged, because they were already screened on CO2e.
- **2026-10-26, same-vintage average (both reviews asked for it; missing from v2's outputs).** Added as a table-only metric, `average_2025`: EIA-930 2025 consumption CO2 with the main analysis's upstream terms.
  - ERCOT 389, PJM 417. There is no US aggregate in the EIA-930 intensity file.
  - Engines and turbines are 1.81–1.89× (ERCOT) and 1.69–1.77× (PJM) of it.
- **2026-10-26, §111.** Verified in the Federal Register: doc. 2026-19071, "Partial Repeal of the Carbon Pollution Standards for Fossil Fuel-Fired Electric Generating Units", published 2026-09-17.
- **2026-10-26 (later), D1b on full-year 2019.** Once 2019 Q4 arrived, D1b was rerun on the full year: Texas 482 vs 492 (−2.1%), Eastern 621 vs 638 (−2.7%). Pass. No 2025 result depends on 2019.
