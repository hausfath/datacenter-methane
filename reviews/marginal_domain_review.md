# Domain review of PLAN_marginal.md (draft v1, 2026-10-26)

Reviewer role: power-system emissions accounting (marginal emission rates, capacity expansion, CEMS/AVERT/Cambium, consequential vs attributional).
Date: 2026-10-26. Files read: `PLAN_marginal.md`, `sources/marginal/MARGINAL_SOURCES.md`, `METHODS.md`, `scripts/emissions.py`, `scripts/cases.py`, `scripts/grid.py`, `data/grid_inputs.json`, `sources/marginal/cambium2024_lrmer_annual_by_region.csv`, `draft_post.md`.

Verification key used below:
- **VERIFIED (this review)**: I read the primary text or computed from the primary file in this session. Sources: Cambium 2024 documentation (NREL/TP-6A40-93005, docs.nlr.gov), the Cambium 2024 workbook in `data/cambium/`, the AVERT v4.3 user manual and AVERT rates workbook (epa.gov), the Holland et al. 2022 article and their 2022 reply (Europe PMC full text), and a PJM Inside Lines post.
- **UNVERIFIED**: from memory, a search snippet, or a law-firm/news summary. Each one is flagged where it appears.

Scratch computations are reproducible from the project CSV. The snippets are in §9.

---

## 0. Bottom line

The plan asks the right question and is better than most published treatments: it uses matched methane on both sides, validates against an external product, and plans a blended metric. But as drafted it has several choices that each lean toward the post's conclusion, and one internal inconsistency. Taken together, they would let a critic say the exercise was built to land where it lands. The most consequential points:

1. **The M1 primary specification (hour-to-hour first differences) measures the wrong margin for a flat load, and it biases the SRMER low.**
2. **The AVERT comparison is on mismatched bases** (AVERT EE rates are per MWh at end use; the plan's numbers are at the busbar).
3. **The Cambium methane "rescaling" is not matched.** It inflates the LRMER by 7 to 8% and contradicts the plan's own line 19.
4. **The long-run side of the figure contains only renewable-heavy definitions.** The one gas-heavy comparator (new NGCC, 455) has been dropped from the figure. That is the single most visible bias, and the user's own rule says to do the opposite.

A rough calculation from verified AVERT numbers (§1.6) puts a fossil-always-marginal SRMER with upstream methane at about **725 (ERCOT), 730 (PJM) and 770 (US) kg CO2e/MWh**. The post's engines and turbines are 705 to 736. So the short-run comparison is plausibly a dead heat, and which M1 specification is primary will decide how it is described. The specification therefore has to be chosen by validation, recorded in the change log, and frozen before the 2024–25 run.

---

## 1. Short-run rate (M1)

### 1.1 MUST-FIX: first differences identify the ramping margin, not the level margin a 24/7 load faces
ΔY_t = β·ΔD_t is identified by hour-to-hour swings. Those swings are mostly the diurnal ramp, met by the resources that follow it: CTs, CCs, imports, hydro and, increasingly, batteries. Baseload and slow units (coal in particular) and unit-commitment decisions (keeping a unit on overnight) are largely absent from Δ-identification.

A data center adds a *level* shift in every hour. Its marginal supply includes exactly the commitment and baseload-dispatch responses that first differences miss.

Storage makes this worse in ERCOT. ERCOT had on the order of 10+ GW of batteries by 2025 (UNVERIFIED figure, but the direction is not in doubt).
- In first differences, batteries absorb a large share of the evening ramp with zero CEMS emissions, so β in those bins is low.
- The recharge energy shows up in other hours as a demand-uncorrelated change, so it is never attributed back.
- Storage is energy-neutral (minus losses), so a sustained load cannot be "met by batteries". A ramp-identified β therefore undercounts the energy-weighted margin.

Holland et al. 2022 do not use first differences (VERIFIED, PMC8872735):
- They "regress hourly emissions on overall hourly load within each interconnection, controlling for month-of-sample and hour-of-day fixed effects", with Newey–West SEs at 48-h lags, load from FERC Form 714, and three interconnections with a load-weighted US value.
- They state that the design "captures all potential grid responses (ramping, dispatch, imports, etc.)".

**Recommendation.**
- Make levels with month-of-sample × hour-of-day fixed effects (Holland) the primary specification. The plan's season × hour bins can be kept as the interaction for an hour-profile.
- Keep first differences as a sensitivity.
- Add a third, daily-total specification: daily CO2 (and fuel heat input) on daily demand, with month-of-sample fixed effects. This nets storage and commitment within the day, which is the closest analogue of a flat block.
- Pre-register that the primary is the specification that passes V-M1a below, not the one that gives the more comfortable answer.

### 1.2 MUST-FIX: validate the method against a same-method published number before AVERT
The user's rule is to reproduce a known published number first. AVERT is a different method:
- AVERT is a statistical dispatch model binned on regional fossil load.
- It assumes fossil generation responds 1:1 by construction, with no imports, curtailment or storage response (VERIFIED, AVERT v4.3 manual: load bins are "fossil-fuel load bins"; a reduction is "relative to hourly fossil-fuel load, and not system demand").

AVERT cannot validate the demand-regressor specification. Holland 2019 can.

**Add V-M1a.** Run the chosen specification on CAMPD 2019 against EIA-930 2019 demand for ERCOT and reproduce Holland's Texas 2019 marginal rate of 1.085 lb/kWh (492 kg/MWh, combustion CO2).
- Suggested tolerance: ±5% or ±2 of their Newey–West SEs, whichever is wider. Holland used FERC 714 load rather than EIA-930, so allow a little extra.
- A US check against 591 kg is possible but needs the three-interconnection build. Do ERCOT first.
- If levels+FE reproduces 492 and first differences do not, that settles the specification.

### 1.3 MUST-FIX: AVERT comparison basis (end-use vs busbar) and a realistic tolerance
VERIFIED from the AVERT v4.3 manual: EE load changes are "adjusted upward by... user's input / (1 – x), where x is the regional average line loss percentage". In 2023, x = 4.58% (Texas) and 7.23% (Eastern Interconnect), and 8.67% (Western Interconnect). Uniform EE rates are therefore per MWh of *end-use* savings. The plan's regression output (per MWh of EIA-930 demand, which is generation-level) is on a different basis.

Harmonized AVERT 2023 values (DERIVED from verified workbook values and the manual's loss factors):

| AVERT 2023 Uniform EE | End-use, kg CO2/MWh | Generation level, ×(1−x) |
|---|---|---|
| Texas | 586.8 | **560** |
| Mid-Atlantic | 618.3 | **574** |
| National | 648.4 | **~600** (approximate: the national value mixes three loss factors) |

Without this harmonization, about 5 to 7 points of the ±10% band are consumed before any method difference appears.

How far apart are AVERT and a Holland-type regression in the same year? This is DERIVED from the verified workbooks:

| Comparison | AVERT 2019 | Holland 2019 | AVERT higher by |
|---|---|---|---|
| Texas, AVERT at generation level | Uniform EE 1,281.7 lb/MWh → 581 end use → 550 generation level | 492 | **+12%** |
| National, AVERT at generation level (EI loss) | 703 end use → ~652 | 591 | **+10%** |
| Texas, AVERT onshore wind (no loss adjustment) | 545 | 492 | **+11%** |

**Recommendations.**
- Compare at generation level (or convert both to busbar).
- Pre-register the *expected* relationship:
  - the fossil-load variant (sensitivity 1) should land within ±10% of loss-adjusted AVERT;
  - the demand-regressor primary should land roughly 5 to 15% *below* AVERT.
- A miss triggers diagnosis, not automatic rejection.
- Do not use ±10% on the demand specification against AVERT. It will fail for valid reasons.

### 1.4 Footprints: PJM and US
**Mid-Atlantic is PJM.** VERIFIED from the AVERT manual:
- Regions are built around a "core" balancing authority: "an AVERT region is based around a 'core' balancing authority (e.g., PJM, MISO, CAISO)".
- Mid-Atlantic covers all of DC, DE, MD, NJ, OH, PA, VA and WV, plus parts of IL, IN, KY, MI, NC and TN.
- Its 2023 fossil load is 467,577 GWh.

That is PJM with a few small BAs attached, so the footprint match is better than the plan and the sources note assume. Make the PJM check pass/fail on the fossil-load variant, with the footprint caveat stated.

**PJM imports (sensitivity 5) is mis-specified.** Regressing Eastern Interconnection CEMS emissions on PJM demand attributes to PJM the emission response to weather-correlated demand in MISO, SERC, NYISO and others. PJM demand is highly correlated with neighbors' demand, so this sensitivity is biased upward and is not an import correction. Two alternatives:
- (a) Regress EI emissions on PJM demand *and* the rest-of-EI demand jointly. This is the spillover design of Graff Zivin, Kotchen & Mansur 2014 (J. Econ. Behav. Organ. 107:248–268, cited in Holland et al.'s 2022 reply, VERIFIED citation). The PJM coefficient is then the interconnection-wide response to a PJM-only shock.
- (b) Report the EI-wide Holland specification as a bracket.

The PJM-only CEMS regression is low-biased by the share of PJM demand changes met by imports. PJM is a net exporter, but its hour-to-hour interchange does flex.

**US.** A single regression of lower-48 CEMS on lower-48 demand sums three asynchronous interconnections. Follow Holland: estimate per interconnection and load-weight.
- Better for this question: also weight by where data-center load is going (ERCOT, PJM_East/Dominion, SERC/Southeast). The national retail-sales weighting describes the average US MWh, not the average data-center MWh.
- Report both weightings.

### 1.5 SHOULD-FIX: data plumbing that can silently bias β
- **Timestamps.**
  - My understanding is that CAMPD/Part 75 hourly records are in the unit's *local standard time*, with no DST shift. UNVERIFIED: my search did not surface the field definition, so check the CAMPD data guide.
  - EIA-930 gives UTC and local time.
  - A one-hour misalignment for ~8 months of the year attenuates any hourly specification and is destructive to first differences.
  - Align everything on UTC, converting CAMPD per plant time zone. PJM spans Eastern and Central (ComEd).
  - Test: the lag-0 cross-correlation of ΔCO2 and ΔD should exceed lags ±1 in every month.
- **EIA-930 anomalies.** The plan keeps imputed and flagged values "as published". Under first differences, one spike creates two large opposite ΔD values with high leverage. Use a documented outlier filter (for example, drop hours where |ΔD| exceeds a robust threshold, or use EIA's flagged-value indicator) and report the sensitivity. Under levels+FE this matters less.
- **CEMS coverage.** Part 75 misses many units under 25 MW (small CTs, recips, oil peakers: exactly the units that are marginal at peaks), some CHP, and non-Part-75 sources. Low-mass-emitter units report default-based hourly values.
  - Compute an annual coverage ratio per region: CAMPD CO2 ÷ EIA-930 production CO2, which METHODS already has (ERCO 343, PJM 322 kg/MWh in 2023).
  - Report it. If coverage is under ~95%, either scale the gas and oil β by the uncovered share of marginal fuel (an upper bound) or note the low bias.
  - PUDL's processed CEMS and Singularity's Open Grid Emissions data fill some gaps (UNVERIFIED current data years).
- **Fuel attribution.** CAMPD "unit fuel type" is the primary fuel, but coal units in PJM and SERC co-fire or have converted to gas. Use the year-specific primary fuel and report heat input from dual-fuel units separately.
  - Internal check: β_CO2 should equal 53.06·β_gasHI + ~95·β_coalHI + ~73–75·β_oilHI within a few percent. CAMPD gas CO2 is largely computed from heat input (Appendix F/G), so a mismatch flags misassignment.
- **CHP.** CEMS heat input for cogeneration includes thermal output. ERCOT's Gulf Coast cogeneration is large. It runs flat, so it mostly drops out of the regressions, but say so.
- **Coal-mine CH4.** The latent issue already flagged in METHODS (ERCOT coal is lignite/PRB at ~0.04 kg/MMBtu, not 0.199) matters more here, because coal is a larger share of the margin than of the average. Use the regional factors from the regional analysis on the SRMER (ERCOT ~0.04; PJM a weighted mix of underground Appalachian ~0.26 and surface coal). The effect is small (single-digit kg) but it is the matched treatment.

### 1.6 Regressor choice, "upper bound" wording, and losses
- **Demand vs fossil load.** Demand is the physically right regressor (curtailed renewables and imports can absorb load). However:
  - (i) Fossil-load regressions are what AVERT and Siler-Evans do.
  - (ii) Demand regressions have weather-driven omitted-variable bias. Hot, sunny hours raise both demand and solar, which lowers β. Adding ΔWind and ΔSolar (EIA-930 by fuel) as controls is a cheap robustness check.
  - (iii) The user's rule says that when a choice is defensible either way, pick the option conservative toward the claim being critiqued.

  Recommendation: either plot the fossil-load value as the SRMER marker with demand as the lower whisker, or keep demand as primary and state explicitly that this departs from the rule, and why.
- **Drop "upper bound".** The fossil-load regressor is not a strict upper bound. Imports from a dirtier neighbor and uncovered small peakers can exceed it. Call it "fossil-always-marginal".
- **Marginal losses.** Cambium's own convention (VERIFIED, documentation §5.1): "Short-run marginal metrics (i.e., cost metrics and the short-run marginal emission rates [SRMER]) use marginal loss metrics, whereas average or long-run marginal metrics use average loss metrics."
  - Apply that here: marginal transmission losses (~2× average, so 5 to 6%) for the SRMER, and 3% average for long-run metrics.
  - This is both internally consistent and conservative toward the critics, so it should be primary, not a sensitivity.
  - EIA-930 demand is generation-level (generation + net imports), so dividing β by (1 − marginal loss) is the right conversion to delivered MWh.
- **Equal-weight mean of 96 bins.** For a flat load, equal hour weights are right. With ~90 observations per bin, though, noisy bins (midday, shoulder seasons) carry full weight. Also report the precision-weighted mean and a pooled estimate with hour-profile interactions.
- **Linearity / GW scale.** A 1 GW block is ~1.5 to 2% of ERCOT load and ~1% of PJM. Holland check linearity with local polynomials (VERIFIED, they do this). Do the same, or run a load-bin specification (Siler-Evans), to show β is stable over the relevant range.

### 1.7 Pre-registered SRMER ranges look plausible, and the result hinges on specification
DERIVED rough check:
- Upstream uplift per MMBtu at L = 2.3%:
  - gas: 4.93 (supply CO2) + 13.1 (CH4) = 18.1 kg CO2e on 53.06, so +34%;
  - coal: CMM 5.9 kg on ~95.5, so +6%.
- With 60 to 70% of the marginal CO2 from gas, the uplift is about +23 to 26%.
- Applied to generation-level AVERT and divided by 0.97:
  - ERCOT ≈ 560 × 1.256 / 0.97 ≈ **725**;
  - PJM ≈ 574 × 1.23 / 0.97 ≈ **728**;
  - US ≈ 600 × 1.24 / 0.97 ≈ **767**.
- A demand specification ~10% lower gives roughly 650 to 700.
- Marginal losses at 6% would add ~3%.

So engines (736) and turbines (705) sit right on the SRMER: above it under one specification, below it under another. The plan's pre-registered interpretation ("roughly a tie for engines and turbines") is honest. But the figure will show a dot on one side or the other of the off-grid line, so the specification choice must be fixed by V-M1a, before the answer is seen.

---

## 2. Cambium LRMER (M2)

### 2.1 MUST-FIX: the precombustion "rescaling" is not matched; replace it with a heat-input reconstruction
The plan scales Cambium's precombustion CH4 by L(1−Lc)/(Lc(1−L)). That is only valid if Cambium's per-MMBtu factor equals c·Lc/(1−Lc) with the project's c. It does not.
- Cambium documentation (VERIFIED, Table 5): gas precombustion CH4 is **571.6 g/MMBtu in 2022, decreasing linearly to 400.2 g/MMBtu in 2030, constant thereafter**, with precombustion CO2 at 6.27 kg/MMBtu.
- The project's `em.upstream_ch4` gives **420.6 g/MMBtu at L = 2.2%** and **440.2 at L = 2.3%**.
- So Cambium's "2.2%" is on a ~36% higher per-MMBtu basis than ours. Its 2030+ factor (400 g) already corresponds to about 2.1% on our basis, not 1.54%.
- The ratio formula therefore multiplies an already-high base and puts more methane per MMBtu on the grid side than on the off-grid side. That violates line 19 of the plan ("methane is treated identically").

**Fix (tested).** Back out Cambium's marginal gas and coal heat input from the two combustion columns, using Cambium's own factors:
- CO2_c = 53.06·G + 95.52·C
- CH4_c = 1.0·G + 11.0·C (g/MMBtu)

Then apply the project's factors: upstream CH4 at L, supply CO2 9.3%, and coal CMM.

Check: the reconstruction reproduces Cambium's own precombustion CO2 (6.27G + 2.94C) to within ~1%. For example, ERCOT 2030: 15.6 predicted vs 15.8 reported; PJM_East 2030: 28.2 vs 28.3. It reproduces precombustion CH4 to within ~1 to 5%, so the method is validated.

2027–2046 simple mean, combustion + precombustion, AR6 GWP100, end-use, kg CO2e/MWh (computed this session from `cambium2024_lrmer_annual_by_region.csv`):

| Region / scenario | Cambium native | Plan's ratio rescale | **Matched reconstruction (L = 2.3%)** | Combustion only |
|---|---|---|---|---|
| ERCOT Mid-case | 147.2 | 157.4 | **145.8** | 111.2 |
| ERCOT High Demand | 167.5 | 179.3 | **165.9** | 126.6 |
| ERCOT Low RE | 160.9 | 171.1 | 159.3 | 124.2 |
| PJM_East Mid-case | 271.6 | 293.2 | **270.3** | 202.0 |
| PJM_East High Demand | 279.5 | 301.8 | **278.1** | 207.7 |
| PJM_West Mid-case | 198.0 | 212.5 | **197.0** | 149.7 |
| PJM_West High Demand | 199.7 | 214.6 | 198.5 | 150.7 |

The native ERCOT Mid-case value of 147.2 reproduces `grid_inputs.json`.

The ratio method inflates the LRMER by ~7 to 8% (+10 to +22 kg). The matched value is within ~1.5 kg of Cambium's native value, because Cambium's 2030+ gas factor happens to sit close to ours at 2.3%.

The ratio method errs toward the critics, but it is not a defensible alternative: it is an inconsistency. Use the matched reconstruction as primary and show native Cambium alongside. Drop the ratio method. Also correct the plan's sentence "This raises the LRMER": in matched terms it barely moves.

### 2.2 SHOULD-FIX: scenario choice. Use High Demand Growth as central and report PJM_East on its own
- The world the post is about (tens of GW of data-center load) is closer to Cambium's High Demand Growth scenario than to its Mid-case. Under the user's rule it is also the conservative choice.
  - ERCOT: 166 vs 146 matched.
  - PJM_East: 278 vs 270.
- Make High Demand the plotted point and show the 8-scenario range as the bar.
- **PJM weighting.** Northern Virginia (Loudoun County) maps to PJM_East (VERIFIED, workbook County Mapping, per the sources note), and that is where PJM's data-center load is concentrated. PJM_East is also the higher value (270 vs 197 Mid-case).
  - A load-weighted East/West mean will land between them, below the 235 unweighted value only if West carries more load. Check the weights.
  - Report load-weighted and data-center-weighted (≈ PJM_East) values. Under the conservative rule, plot the data-center-weighted one.

### 2.3 Busbar conversion and the extra 3% loss: fine, and immaterial
VERIFIED from the documentation:
- The LRMER uses the *average* distribution loss rate. The workbook's annual "Distribution Loss Rate" is 0.036 for ERCOT, PJM_East and PJM_West.
- "Busbar refers to the point where bulk generating stations connect to the grid."
- PLEXOS represents "Inter-BA transmission ... as pipe flow with constant loss rates, with no intra-BA transmission losses."

So converting to busbar and then applying the project's 3% transmission loss is not a double count of intra-BA losses. The net effect is ×(1−0.036)/(1−0.03), about −0.6%. Note it and move on. The workbook's Levelized LRMER tab also has an end-use/busbar switch; use it as a cross-check.

### 2.4 SHOULD-FIX: how to characterize the pre-OBBBA bias. It is two stale policies, not one, and the magnitude is unknown
- **IRA credits.** VERIFIED (documentation p.12–13, quoted in the sources note): in all scenarios "IRA's tax credits for qualifying generation are represented as not phasing out." None of the eight scenarios is a no-credit case, so the scenario range does not bracket OBBBA.
- **EPA Section 111 (May 2024).** VERIFIED (documentation, §3): "In 2032 and for every year thereafter, the emissions rate ... of a state's coal fleet must be less than or equal to the emissions rate of a coal-carbon capture and storage (CCS) plant with a 90% capture rate. Because coal-CCS is not available ... coal is therefore induced to retire after 2032". Also: "starting in 2032, the investment in new gas plants ... is evaluated based on anticipated operation below a 40% capacity factor."
  - Per law-firm summaries (Davis Polk, Jackson Walker, Beveridge & Diamond; UNVERIFIED against the Federal Register), EPA finalized a partial repeal of the 2024 standards in September 2026. It removes the existing-coal guidelines and CCS requirements, effective 16 November 2026.
  - The plan does not mention this assumption at all. It is a major driver of the post-2032 drop in the LRMER, and most of the 2027–2046 window is after 2032.
- **Other assumptions with known direction:**
  - "Any announced or anticipated behind-the-meter generator investment is not reflected in this modeling" (VERIFIED).
  - Near-term builds are queue-constrained only through the 2028 solve (VERIFIED).
- **Assumptions that partly offset:** current gas-turbine capital costs and backlogs are far above ATB 2024 assumptions, which raises the cost of the gas alternative in a re-run and pushes toward renewables. Solar and storage tariffs and FEOC rules push the other way. (UNVERIFIED in magnitude.)
- **Suggested wording:** "Cambium 2024 assumes IRA credits never expire and EPA's 2024 coal and new-gas rules take effect. Both have since been reversed or largely repealed. Both push the modeled LRMER down, especially after 2032; we cannot quantify by how much because no post-OBBBA Cambium exists."
- **Optional bracket:** a pre-IRA Cambium vintage (Cambium 2021, published before August 2022; UNVERIFIED that it contains no IRA) gives a no-IRA-credit LRMER, with old cost and load assumptions. Show it as a sensitivity labelled as such.

The plan's statement "Both of these bias the LRMER low" is right for the credits and the 111 rule. It is **not established for the GW-scale point** (§2.5).

### 2.5 SHOULD-FIX: GW-scale load is inside Cambium's perturbation; correct the caveat
VERIFIED (documentation §6.4): "In Cambium 2024, the 2025 solve has a 1% scalar load perturbation, whereas all other solve years have a 5% scalar load perturbation". The perturbation is "a scalar increase in load across all hours", which matches a flat load.
- 5% of ERCOT end-use load in the 2030s is roughly 25 TWh/yr, or about 3 GW average (DERIVED from approximate ERCOT load; the exact Cambium load is not checked).
- So a single 1 to 2 GW campus is *smaller* than the perturbation. The plan's caveat "Cambium assumes a small increment of load, not GW-scale blocks" is wrong for a single campus.
- What is outside Cambium's envelope is the aggregate: 50 to 90 GW of BTM-plus-grid data-center load. That looks like a different base scenario, not a perturbation, which is another reason to centre on High Demand Growth.
- The perturbation is scalar across all regions at once, not a localized block. That matters for interregional flows (PJM_East) but has no clear sign.

### 2.6 Anticipated or unanticipated? The 2027–2046 window
VERIFIED (workbook guidance): "Cambium data sets are designed primarily for long-term, forward-looking analysis... If analysts are predominately interested in the near term (i.e., within the 2020s), they would likely be better served by drawing from recent empirical observations rather than Cambium data." Also: for unanticipated interventions, use "short-run metrics for the initial period ... (e.g., 3-5 years)".

A data center that goes off-grid *because* the grid cannot connect it in time is, by construction, a load the grid planners have not yet accommodated. The 2027–2029 portion of the window is in the regime where NREL itself says to use empirical short-run data.

So the plotted Cambium point should be the **blended** metric, not the pure LRMER (§3.5).

---

## 3. Build margins (M3, M4) and the "new-build" comparator

### 3.1 What M3 and M4 actually measure
- **Recent build margin (M3)** is the average emission rate of what the grid *happened* to add, which in ERCOT is mostly solar, wind and storage built on merchant and IRA economics. It is not what the data-center load *induces*. Gagnon & O'Shaughnessy say so directly (VERIFIED, sources note): "LRMERs are not equivalent to the build margin".
- **The capacity constraint is missing.** Energy-matched build margins ignore that a flat load needs firm capacity at net peak (ERCOT winter mornings, PJM summer and winter peaks). In PJM, new load raises the capacity requirement, which is met by ELCC-accredited capacity, where solar's accreditation is low (UNVERIFIED specific ELCC values). An energy-matched solar-heavy build margin is therefore a floor on emissions, not a central estimate.
- **The timing mismatch is real and one-directional.** Solar MWh do not serve a 24/7 load at night. The night-time residual is met by the operating margin. A simple correction: "build margin for daytime energy, SRMER for the rest". Use hourly EIA-930 BA solar and wind profiles to compute the fraction of a flat load that recent renewable additions could cover hour by hour, and fill the remainder at the hourly SRMER. That is a defensible "hourly-matched build margin" and is cheap given the M1 outputs.
- **Storage.** Excluding batteries from generation is fine. But their charging is supplied by the operating margin in charging hours, minus round-trip losses (~15%). In an hourly-matched version, charge energy should carry the charging-hour SRMER.
- **Additionality.** Renewables in the recent sample would mostly have been built anyway. This is a strong reason not to call M3 "new-build marginal" in the figure. Label it "average of recent additions" and keep it in the table.

### 3.2 M4 planned build margin
- The 2026–2028 window *under-represents* the gas being procured for data centers, because turbine backlogs push those CODs to 2028–2031. Examples:
  - The sources note: Entergy Louisiana / Meta, three 1×1 CCs totalling 2,262 MW, in service late 2028 to 2029 (order VERIFIED; dates SECONDARY).
  - Georgia Power: roughly two-thirds gas in the December 2025 certification (UNVERIFIED).
  - EIA expects only 6.3 GW of gas in 2026 against 43 GW of solar (VERIFIED by tool).
- Extend M4 to 2026–2030 or use the latest 860M planned years in full.
- **Slippage: hindcast it rather than assume it.**
  - Take an 860M vintage from about two years ago (for example, December 2023) and compute the realization rate by technology and status for units planned for 2024, against EIA-860 2024 actuals.
  - Apply those rates to the current 860M.
  - This is a cheap, data-based fix for "planned renewables slip more than gas".

### 3.3 SHOULD-FIX: the most defensible new-build comparator for a 24/7 GW load in 2026–2030
A domain expert's answer: there is no single build margin. The defensible comparators are:
- (a) **Short-run operating margin for the first several years**, likely extended where large loads delay retirements (§4).
- (b) **What utilities are actually building for hyperscaler tariffs.** Examples: Entergy/Meta (2.26 GW CC + 1.5 GW solar procurement), Georgia Power, Dominion, AEP. That is a gas-heavy portfolio with some solar and storage, on the order of 300 to 455 kg CO2e/MWh depending on the mix.
- (c) **Additional clean-firm procurement**, if the buyer contracts it: restarts (Palisades, Crane/TMI, Duane Arnold), new geothermal, hourly-matched portfolios. Consequential emissions approach zero *only if* the procurement is additional and hourly-matched. PPAs with existing nuclear (Clinton, Susquehanna) reallocate rather than add.

Recommendations:
- **Add a "utility procurement for large loads" row**, built from documented IRP and certification filings: at minimum Entergy/Meta, from the LPSC order already in hand, plus one PJM case. Weight by energy, using the plan's capacity factors and heat rates.
  - If documentation is thin, use a clearly flagged stylized mix: two-thirds gas CC, one-third solar+storage by energy.
- **Put the new grid NGCC (455) back in the figure** as the all-gas bound. Dropping the one gas-heavy long-run comparator while plotting three renewable-heavy ones is the most visible bias in the plan (§6).
- **Show "grid + additional 24/7 clean procurement" as a labelled lower bound**, or mention it in text. It is the case the hyperscalers' own procurement teams will cite.

### 3.4 Tool 07 sample details
- The 5-unit / 20% rule as quoted from the Verra draft is fine.
- Steps (d)–(f) (age and capacity-addition conditions) are unread. State that.
- For CCs, sum CT and CA fuel and generation at plant–prime-mover level in EIA-923. Generator-level fuel allocation for CCs is unreliable.

### 3.5 SHOULD-FIX: the blend belongs in the figure, with a lag set by real interconnection timelines
Gagnon & O'Shaughnessy's w-blend is the only approach with institutional guidance for new loads. Their worked example uses w = 0.15 for a 3-year lag (VERIFIED).
- Large-load interconnection and new-capacity lead times in 2026 are 3 to 7 years (UNVERIFIED range; turbine backlogs alone push new gas to 2029–2031).
- Use w = 0.15, 0.25 and 0.35 (3, 5 and 7-year lags on a 20-year load).
- Plot the w = 0.25 blend as a marker, with the 0.15–0.35 range as its bar.
- Use the matched High Demand LRMER for the post-lag years, and disclose the Amazon funding.

---

## 4. Missing metrics and sources critics will raise

**Should-fix:**
1. **Holland et al. reply (PNAS 2022, e2214219119; VERIFIED full text, PMC9894178).**
   - They interpret their estimates as short run and say "a decade hence is reasonable to interpret as short run".
   - On coal and gas: "We remain skeptical as long as coal and natural gas remain part of the generation mix."
   - They describe NREL's long-run approach as assuming "an array of complementary policies take place", and conclude "there is room for both. A range of possible impacts is most informative".
   - This is the critics' best citation. It also supports showing both horizons rather than choosing one, which is what the post-script should do.
2. **PJM's own marginal emission rates.** VERIFIED (PJM Inside Lines, 2021 report): the marginal unit is "the final generation resource committed during a dispatch interval". PJM reports on-peak and off-peak marginal CO2 rates annually. A search snippet gives 2021 values of 1,089 / 1,037 lb/MWh (494 / 470 kg; UNVERIFIED numbers).
   - These are price-setting-unit rates, conceptually different from a quantity regression and well below AVERT Mid-Atlantic. Critics and PJM-area commenters will cite them.
   - Retrieve the 2024 or 2025 report (pjm.com path; ftp.pjm.com did not resolve) and show it as a PJM cross-check.
   - The same PJM report gives marginal-fuel shares (2021: CC 59.75%, coal 14.15% of intervals; VERIFIED in the Inside Lines post). That is a direct test of the plan's "coal still marginal at night" expectation.
3. **eGRID non-baseload output rates** are already in `data/grid_inputs.json`: ERCOT 568, PJM 649, US 626 kg CO2e/MWh (combustion, generation basis). This is EPA's crude operating-margin proxy and is widely cited by non-specialists. Add it to the table with upstream added on the same basis; it costs nothing.
4. **Hydrogen 45V literature** (an analogous large, flat, new load). Ricks, Xu & Jenkins (2023, Environ. Res. Lett. 18:014025; from memory, UNVERIFIED citation details) and the "three pillars" (additionality, deliverability, hourly matching) debate. These are the most developed consequential analyses of exactly this problem, and both sides will invoke them. Cite them for the point that annual-matched or build-margin accounting understates induced emissions from flat loads.
5. **Coal-retirement deferrals and large loads.**
   - DOE 202(c) orders kept J.H. Campbell (MISO) and Eddystone (PJM) running in 2025 (from memory, UNVERIFIED).
   - The sources note has Georgia Power extending Scherer and Bowen (SECONDARY).
   - Treat this as extending the short-run regime: raise w in the blend as a sensitivity.
   - Optionally, count PJM and ERCOT units whose 860M planned retirement date moved later between vintages.
6. **Same-vintage grid averages.** The SRMER will be 2024–25 and the "average as posted" is eGRID 2023. ERCOT's EIA-930 production intensity fell from 343 to 311 kg/MWh between 2023 and 2025 (METHODS). A row mixing vintages exaggerates the average-to-marginal gap.
   - Plot the posted 2023 average for continuity, and add the 2024/25 EIA-930 consumption-basis average already in the pipeline.
   - Recheck whether eGRID2024 has been released. The sources note says a mirror lists it (UNVERIFIED), and METHODS says it had not been as of 24 October.

**Optional:**
7. **Locational marginal emissions (REsurety, WattTime MOER).** No public annual values exist (sources note). Mention that nodal LMEs differ by location within a BA and that the regression gives a BA average. Do not try to acquire them.
8. **Data-center flexibility.**
   - Knittel, Senga & Wang (NBER w34065, in the sources note) find that flexible operation lowers costs but can raise emissions.
   - The Duke "Rethinking Load Growth" study (Norris et al. 2025; UNVERIFIED) argues that curtailable large loads can connect sooner, which shortens the SR window and the off-grid rationale.
   - One sentence each.
9. **GHG Protocol AMI and the Emissions First vs 24/7 debate.** The sources note covers it adequately: no adopted rule as of October 2026. When citing NREL's report, also note that the main corporate proponents of marginal accounting are hyperscalers.
10. **Off-grid counterfactual timing (framing).** If the off-grid plant exists because the grid cannot serve the load until year X, then the grid alternative for years 0 to X is not "grid power at SRMER". It is "wait". After X, many BTM plants become backup or bridge. The SR comparison is cleanest for loads that *could* connect now. Say this in the post-script, since it cuts both ways.

---

## 5. Tool 07: how much weight

**Moderate-to-low as evidence about which number is right; moderate as rhetoric.**
- The OM-only rule for consumption-increasing projects is in a 2024 Verra *draft* (VERIFIED via the sources note), not in verified CDM TOOL07 text.
- Crediting standards set conservative factors for credit issuance (the same draft uses a 1.3 t CO2/MWh default for imports). They are not designed to estimate the true consequential impact of a load.
- My recollection (UNVERIFIED) is that, in CDM practice, project *consumption* of grid electricity is governed by TOOL05, which allows a conservative default or the TOOL07 combined margin. Check this if you can get to the UNFCCC site in a browser.

Recommendations:
- Report the convention in one sentence in the post-script.
- Concede that it aligns with the critics' short-run framing.
- Do not let it decide the headline.

The GHG Protocol has adopted nothing: its consultation summary says the consolidated consultation is slated for Q2 2027 (sources note). The plan's current treatment is about right. Downgrade "must say so explicitly" to "should say so briefly".

---

## 6. Framing and pre-registration: is the plan set up to give an honest answer?

Audit of choices against the user's rule (prefer the option conservative toward the post's claim that the grid is cleaner):

| Choice in plan | Direction | Recommendation |
|---|---|---|
| First differences as primary SRMER | Toward post (low β; misses commitment, baseload and storage netting) | Levels+FE primary, chosen by V-M1a (§1.1–1.2) |
| Demand regressor as primary | Toward post (lower) | Physically defensible. Show fossil-load as the upper whisker, or justify the departure explicitly |
| 3% loss on SRMER, 6% as sensitivity | Toward post | Marginal losses (5–6%) primary for SR, per Cambium's own convention |
| New NGCC (455) dropped from figure | Toward post (the only gas-heavy long-run comparator removed) | Restore it; add a utility-procurement row |
| Cambium Mid-case central | Toward post (ERCOT 146 vs 166) | High Demand central |
| PJM East/West unweighted or load-weighted | Toward post (vs PJM_East 270) | Report data-center-weighted; plot it |
| w = 0.15 central | Toward post | w = 0.25 central, 0.15–0.35 range |
| Energy-matched build margins labelled "new-build marginal" | Toward post | Label as "average of recent/planned additions"; add an hourly-matched version |
| Cambium ratio rescale | Toward critics, but inconsistent | Replace with matched reconstruction |
| eGRID 2023 average (dirtier than 2025 in ERCOT) | Toward critics (raises the average) | Keep for continuity; add same-vintage average |
| National CMM for ERCOT coal | Toward critics (small) | Regional CMM |

**Pre-registration issues:**
- The long-run "expectations" (Cambium 150–250) were already known, since `grid_inputs.json` already contains them. Say so. They are not predictions.
- The pre-written interpretation "Under every long-run definition, all four off-grid options emit more than the grid" is close to true by construction given the chosen definitions. With the NGCC and utility-procurement rows restored, the honest pre-registered statement is more nuanced:
  - Engines and turbines exceed every long-run comparator, including all-gas new build.
  - SOFC and on-site CC tie a gas-heavy new build and exceed renewable-heavy ones.
  - On the short-run margin, engines and turbines are approximately tied, and SOFC and CC are below.
- Write that now, before running anything.
- Add a pre-registered **decision**: what the post-script will say under each outcome of the SRMER test, using the existing MC tie-band machinery from `cases.py`. Without it, the SRMER tie will be described after the fact.

The plan's concession paragraph (the SR view is valid for the first few years of an unanticipated load, which is the off-grid builders' argument) is good and should stay. It should be paired with the counterfactual-timing point in §4.10.

---

## 7. Figure design

A single dot-plot row per region, with five or six markers, CI bars and four vertical reference lines, will be crowded and hard to read on social media. Suggested changes:

- **Layout.**
  - Three small-multiple panels (ERCOT, PJM, US), each with *metrics as rows*, ordered by horizon: average (2023 as posted; same-vintage 2025), SRMER, blend (w = 0.25), Cambium LRMER, utility procurement, new NGCC, recent build, planned build.
  - Group the short-run and long-run rows with a light bracket or a background tint.
  - Alternatively, one panel with metrics as rows and the three regions as offset, color-coded dots per row. That is better for the "which definitions cross the off-grid lines" read.
- **Off-grid as two shaded vertical bands, not four lines:**
  - engines/turbines 705–736;
  - SOFC/on-site CC 460–475.
  - Label the bands at the top of each panel. Four closely spaced vertical lines (705/736 and 460/475) will produce overlapping labels.
- **Color by metric family, not by region:** average neutral grey, short-run one hue, long-run another, new-build gas a third. Ranges as thin bars:
  - SRMER: 90% CI plus a whisker to the fossil-load variant;
  - Cambium: scenario range;
  - blend: w range.
- **Title and subtitle bound to computed values.** For example: "Off-grid engines and turbines are roughly level with the grid's short-run margin and well above every long-run measure." Only use this wording if the numbers say so.
- **Text.** Label the x-axis "kg CO2e per MWh delivered (GWP100, methane leak rate 2.3% on both sides)". Footer: vintages, Cambium pre-OBBBA and pre-111-repeal caveat, AVERT basis.
- Check title/subtitle spacing per the memory note on figure spacing, and keep CI bars from colliding with markers.

---

## 8. Prioritized list

**Must-fix (before M1–M4 run)**
1. M1 primary specification: levels + month-of-sample × hour fixed effects (Holland), with first differences and daily-total as sensitivities. Choose the specification by validation, not by result (§1.1).
2. Add V-M1a: reproduce Holland 2019 Texas (492 kg CO2/MWh) with the chosen specification, ±5% or 2 SE (§1.2).
3. Put AVERT on a generation basis: ×(1−x), x = 4.58% Texas and 7.23% EI. Pre-register the expected AVERT relationship for both regressors (§1.3).
4. Replace the Cambium ratio rescale with the matched heat-input reconstruction. It is tested: it reproduces Cambium precombustion CO2 to ~1%, and the ratio method overstates by 7–8% (§2.1).
5. Restore the new NGCC (455) to the figure and add a utility-procurement row. Revise the pre-written long-run interpretation (§3.3, §6).
6. Pre-register the post-script wording for each SRMER outcome, because the short-run comparison is plausibly a tie (§1.7, §6).

**Should-fix**
7. Align timestamps on UTC: CAMPD (probably local standard time; UNVERIFIED) vs EIA-930. Filter EIA-930 outliers (§1.5).
8. Fix PJM imports sensitivity 5: joint PJM and rest-of-EI regressors (Graff Zivin et al. 2014 design). Build the US value from three interconnections and also weight it by data-center location (§1.4).
9. Report a CEMS coverage ratio; use regional coal-mine CH4; run the β_CO2 fuel-consistency check (§1.5).
10. Marginal losses (5–6%) primary for the SRMER, 3% for long-run metrics (§1.6).
11. Cambium: High Demand central, PJM_East (data-center-weighted) plotted. Characterize the bias as IRA credits + Section 111 (repealed September 2026 per law-firm summaries, UNVERIFIED). Correct the GW-scale caveat: a single campus is smaller than Cambium's 5% perturbation (§2.2–2.5).
12. Blend in the figure: w = 0.25 central, 0.15–0.35 range (§3.5).
13. Hourly-matched build margin; extend M4 to 2030; hindcast 860M slippage. Label build margins as averages of additions (§3.1–3.2).
14. Add PJM's own marginal rates, eGRID non-baseload, same-vintage averages, the Holland reply, and the 45V literature (§4).
15. Downgrade Tool 07 to one sentence (§5).

**Optional**
16. Pre-IRA Cambium vintage as a no-credit bracket (§2.4).
17. Flexibility, LME and off-grid counterfactual-timing notes (§4).
18. Figure redesign as in §7.

---

## 9. Reproducibility notes for the numbers above
- **Matched Cambium reconstruction.**
  - Solve [53.06, 95.52; 1.0, 11.0]·[G, C] = [co2_comb_kg_MWh, ch4_comb_g_MWh] per row of `sources/marginal/cambium2024_lrmer_annual_by_region.csv`.
  - Matched precombustion = G·(53.06·0.093 + em.upstream_ch4(0.023)·29.8) + C·0.199·29.8.
  - Interpolate 2025–2050 (5-year steps) to annual and take the mean over 2027–2046.
  - The ratio method uses Lc linear from 2.2% (2022) to 1.54% (2030), with k = L(1−Lc)/(Lc(1−L)) applied to ch4_pre.
- **AVERT.**
  - Rates from `avert_emission_rates_04-11-24_0.xlsx`: 2019 sheet row "Texas", Uniform EE 1,281.73 lb/MWh; national 1,549.56. 2023 Texas 1,293.73, Mid-Atlantic 1,363.18, national 1,429.48.
  - Loss factors from AVERT v4.3 user manual Table 2.
- **Cambium documentation quotes:** NREL/TP-6A40-93005 (docs.nlr.gov/docs/fy25osti/93005.pdf), §3 (111 rule; near-term investment; BTM exclusion), §4.1, §5.1 (loss conventions and footnote 13), §6.4 (perturbation sizes), Table 5 (precombustion factors).
- **Holland et al.:** PMC8872735 (specification and data) and PMC9894178 (reply).
