# Methods review of PLAN_marginal.md (draft v1, 2026-10-26)

Reviewer: statistics/methods reviewer (Claude subagent), 2026-10-26. Only this file was written; PLAN_marginal.md and all other files are unchanged.

Read: `PLAN_marginal.md`, `sources/marginal/MARGINAL_SOURCES.md`, `METHODS.md`, `scripts/emissions.py`, `scripts/cases.py`, plus `scripts/grid.py` (Cambium context function) and the local Cambium 2024 workbook (`data/cambium/Cambium24_Workbook.xlsx`, guidance tab and Levelized LRMER tab).

Computations were run inline with python3.13 against `sources/marginal/cambium2024_lrmer_annual_by_region.csv` and `emissions.py`. Nothing was saved to the project. Anything marked **[verify]** is from my own knowledge, was not checked against a primary source in this session, and must be checked before it is relied on.

## Bottom line

The overall architecture is sound: the short-run, long-run and build-margin estimates are built from marginal heat input by fuel, and methane is treated the same way on both sides. Most of the identification and data problems below are standard for this literature and can be fixed. The plan has five weaknesses that would make the headline fragile:

1. **The Cambium methane rescaling is miscalibrated.** The algebra is right, but the leak rate Cambium actually used, inferred from its own numbers, is not the documented schedule. As written, the plan's adjustment inflates the "matched-L" long-run rate by 11 to 22 kg/MWh. The correct adjustment is 2 to 4 kg/MWh (§7).
2. **The short-run regression conditions on the wrong things.**
   - Wind and solar are not controlled for.
   - The PJM "imports" sensitivity omits rest-of-interconnection demand, so as written it is biased upward by a large factor.
   - The national number pools three separate interconnections.
   - The contemporaneous hourly estimator counts storage and hydro responses as zero-emission, but for a persistent flat load that energy has to be replaced later.
3. **The validation can pass for the wrong reasons.** The one pass/fail test (fossil-load regressor vs AVERT) shares no timestamps with EIA-930, so it cannot detect the alignment bug that would most damage the primary spec. Its ±10% band is about as wide as the margin the result will be judged on, and AVERT's end-use loss gross-up consumes half of it.
4. **The bootstrap CI will look falsely precise.** The real uncertainty is in the choice of specification. The figure should show a pre-registered specification envelope.
5. **The pre-registered expectations are probably too low for ERCOT.** Translating AVERT's 2023 Texas rate into the project's CO2e accounting gives about 770 to 810, against a pre-registered 600 to 720. On that arithmetic, engines and turbines (705 to 736) would come out below the short-run marginal grid, not tied with it. The interpretation section needs a wording rule for that outcome before anything runs.

---

## MUST-FIX

### MF1. Cambium precombustion CH4: replace the gas term rather than rescale it with the documented Lc (item 7)

**The formula itself is right.** `em.upstream_ch4(L) = c·L/(1−L)` with c = 18.70 kg CH4/MMBtu. The ratio of upstream CH4 at L to that at Lc is therefore L(1−Lc)/(Lc(1−L)), which is exactly the plan's formula. Writing Cambium's leak rate as an implicit fraction rather than per delivered MMBtu changes the ratio by less than 1%.

**The documented Lc does not describe Cambium's numbers.** I backed out Cambium's gas precombustion CH4 per MMBtu from the workbook's own columns:
- Gas and coal fuel per MWh are solved from combustion CO2 and N2O, using 40 CFR 98 factors: gas 53.06 kg CO2 and 0.1 g N2O per MMBtu; coal about 95.5 kg and 1.6 g.
- Cambium's combustion CH4 and N2O per gas-equivalent MMBtu come out at 1.0 g and 0.10 g in gas-only years. That matches Table C-2, which confirms Cambium uses these factors.
- I then regressed precombustion CH4 on the gas and coal fuel across the 18 GEA regions, year by year:

| Year | Implied gas precombustion CH4 (kg/MMBtu) | Coal (kg/MMBtu) | R² | Equivalent L in this project's parameterization |
|---|---|---|---|---|
| 2025 | 0.478 | 0.206 | 0.96 | 2.49% |
| 2030 | 0.391 | 0.196 | 0.98–0.99 | about 2.05% |
| 2035–2050 | 0.400 | ≈0 (no coal) | 1.000 | 2.09% |

For comparison:
- Project L = 2.3% gives 0.440 kg/MMBtu.
- The plan's documented Lc gives 0.372 in 2025 (Lc = 1.95%) and 0.292 from 2030 on (Lc = 1.54%).

So Cambium's gas factor falls about 16% from 2025 to 2030 (0.478 to 0.40), not the 21% the "−30% by 2030" schedule implies over that window. Its level is also higher than our formula gives at the documented Lc. Cambium evidently converts "2.2%" to kg/MMBtu on a different basis from ours. One candidate is national supply-chain CH4 divided by gas consumed, but I have not verified this.

**Consequences for the plan as written.** Its multiplier runs 1.29 (2027) → 1.43 (2029) → 1.505 (2030 onward), when the data call for about 1.10 from 2030 onward and about 0.92 in 2025. That is, at 2025 Cambium is already above our 2.3%. The table compares the three versions, all on the Mid-case, 2027–2046 simple mean, kg CO2e/MWh end-use:

| GEA | As published | Plan's rescaling | Calibrated replacement | Calibrated, plus Cambium's gas supply CO2 set to f = 0.093 |
|---|---|---|---|---|
| ERCOT | 147.2 | 158.0 (+10.7) | 149.1 (+1.8) | 146.4 |
| PJM_East | 271.6 | 293.3 (+21.7) | 275.7 (+4.1) | 270.5 |
| PJM_West | 198.0 | 212.8 (+14.8) | 200.7 (+2.7) | 197.2 |

The direction is conservative toward off-grid gas, so it will not flip any long-run verdict. It does, however, mislabel the rescaled number as "matched L". It also overstates by 7 to 8%, which is visible on the dot plot.

**Fix:**
- Infer the gas fuel per MWh G_t from combustion CO2 and N2O, as above, or take it from the Scenario Viewer's generation by technology if that can be reached.
- Compute `ch4_pre_matched = ch4_pre − a_t·G_t + em.upstream_ch4(0.023)·G_t`, where a_t is Cambium's implied gas factor (0.478 / 0.391 / 0.400). Do this year by year on the 5-year points, then interpolate.
- Leave the coal part alone. Cambium's implied coal factor, about 0.20 kg CH4/MMBtu, matches this project's CMM of 0.199. This independently checks the decomposition, and it also means that applying the plan's ratio to total `ch4_pre` would wrongly scale coal-mine CH4 by the gas ratio.
- Record the back-out as a validation step in METHODS, with its R².
- If the Cambium documentation gives an explicit kg/MMBtu table, quote it and use it instead.

**Also harmonize f (should-fix level).** Cambium's gas precombustion CO2 is 6.27–6.47 kg/MMBtu, which is 11.8–12.2% of 53.06, whereas `grid_avg()` uses 9.3%. Replacing it moves the result by −2.7 to −5.2 kg/MWh. Either harmonize, or state that the LRMER carries a 2.5-point-higher supply-chain CO2 factor than the other grid metrics.

### MF2. Control for wind and solar in the short-run regression; state the curtailment trade-off (item 1)

Fossil output responds to net load, not demand. Within a season × hour bin, day-to-day variation in ΔD is correlated with ΔSolar and ΔWind, because they share weather:
- On clear, hot days the morning AC ramp and the solar ramp are both larger.
- Cold fronts bring both wind and heating load.

Omitting ΔW biases β_b by γ_W·cov(ΔD, ΔW)/var(ΔD). Here γ_W is roughly the negative of the marginal fossil rate. The sign of the bias flips between sunrise and sunset bins, so the bins do not cancel reliably, and the equal-weight mean inherits whatever is left.

EIA-930 BALANCE files carry hourly generation by fuel for each BA, including wind and solar.

Pre-register three variants:
- (a) ΔD only, as in the plan.
- (b) ΔD plus ΔWind and ΔSolar.
- (c) Δ(net load) as the regressor.

These involve a trade-off. Actual wind and solar output partly reflects curtailment, and curtailment responds to demand: in ERCOT's spring midday hours, extra demand reduces curtailment. Controlling for actual output therefore removes part of the channel the plan deliberately keeps, which biases (b) toward a higher rate. Leaving them out confounds the estimate with weather. The defensible treatment is to report (a) and (b) as an interval. If ERCOT's available-capacity data (HSL, or uncurtailed potential) can be obtained cheaply, a control based on it removes the trade-off.

Pick one primary before running. I would choose (b), because the confounding is first-order in ERCOT and the curtailment channel matters only in a minority of hours.

### MF3. Time-alignment and timestamp conventions, with a pre-registered lag diagnostic (item 4)

In a first-difference regression, a one-hour offset between CEMS and EIA-930 does more than add noise. During ramps, ΔY_t paired with ΔD_{t±1} is a different quantity, so β shrinks toward zero and the hour bins get scrambled. Several conventions have to be pinned down from the data dictionaries rather than assumed:
- **CAMPD hour convention [verify in the CAMPD data dictionary].** My understanding is that Part 75 hourly data are hour-beginning (hour 0 = 00:00–01:00) in local standard time with no daylight saving. Do not build on that until it is confirmed.
- **EIA-930 [verify].** I believe it publishes both UTC and local time "at end of hour", i.e. hour-ending. If both of these are right, there is a one-hour shift in addition to the time-zone conversion.
- **Plant time zones.** These must be assigned per plant, from location rather than from the BA. PJM spans Eastern and Central (ComEd). The lower-48 spans four zones, and some states are split (IN, KY, TN, FL, MI, TX).
- Convert everything to UTC hour-ending before merging. Bin by local standard hour of the BA.

**Pre-registered diagnostic.** Compute the cross-correlation of ΔCO2 and ΔD at lags −3 to +3 for each region and year. It must peak at lag 0. Report the lag-0 to lag±1 ratio. If the peak is off zero, stop.

Check the DST transition days separately: 23- and 25-hour days in any series that is on local clock time.

### MF4. PJM imports sensitivity as written is badly biased; fix the US aggregation (item 1)

**Sensitivity 5.** The plan regresses Eastern Interconnection CEMS emissions on PJM demand alone. PJM demand and rest-of-EI demand are strongly correlated hour to hour, through shared diurnal shape and weather, and rest-of-EI demand is roughly four times larger. A regression of EI emissions on PJM demand alone therefore has a slope of about MER × cov(ΔD_EI, ΔD_PJM)/var(ΔD_PJM). That could be several times the true PJM marginal rate.

Fix: regress EI emissions on ΔD_PJM and ΔD_rest-of-EI jointly (the Graff Zivin, Kotchen and Mansur 2014 approach, J. Econ. Behav. Organ. **[verify citation]**). The coefficient on ΔD_PJM is then the system-wide response to PJM load. It should be the primary PJM spec, not a sensitivity, because a PJM data center's emissions anywhere in the EI count. The PJM-only Y is downward-biased whenever imports respond. Expect wider confidence intervals because of the collinearity. Report the variance inflation factor (VIF).

**US.** A single lower-48 regression pools three systems that do not share dispatch. It weights each interconnection by its share of var(ΔD), not by load, and the time-zone offsets put different hours into one bin. Compute US instead as the load-weighted mean of ERCOT, EI and WECC estimates. This follows Holland et al. Note that AVERT's national value is weighted by fossil generation, so for the validation compare against our regional estimates combined with AVERT's fossil-generation weights.

### MF5. Validation (V-M1) can pass for the wrong reasons; add a real reproduction (item 5)

How the current test can pass falsely:

| Mechanism | Effect |
|---|---|
| Sensitivity 1 regresses CEMS CO2 on CEMS gross load. Both share timestamps and units. | It cannot detect the CAMPD/EIA-930 alignment errors (MF3), EIA-930 anomalies or regressor problems that affect the primary spec. A pass validates the CEMS aggregation and the unit-to-BA mapping, nothing more. |
| AVERT EE rates are per MWh at end use, with a T&D gross-up (MARGINAL_SOURCES §1.1). | That is about 5–7% **[verify AVERT's regional loss factor in the v4.3 user manual]**, half the ±10% band. It must be removed before comparison. |
| Gross vs net. | Sensitivity 1 gives kg per gross MWh. Station service is about 2–8% depending on technology. The two biases offset against the loss gross-up, so a pass can hide both. |
| The national comparison is a pooled lower-48 regression vs AVERT's fossil-generation-weighted mean of 14 regions. | These are different estimands. |
| ±10% ≈ ±60 kg/MWh. | That is comparable to the gap between the expected SRMER and the 705–736 off-grid values, i.e. the decision margin. |
| AVERT bins by fossil-load level (levels-like); the plan uses first differences. | A disagreement could be specification, not error. |

Fixes:
1. **Deflate AVERT to the busbar basis** with its own loss factor. Put both sides on a net-generation basis. For sensitivity 1, convert CEMS gross to net with plant-level EIA-923 net / CEMS gross ratios.
2. **Add a reproduction of a published regression number with its own spec.** Holland et al. 2022, 2019 data: Texas 1.085 lb/kWh, US 1.303, with Newey-West SEs in the SI. Use their specification: levels, month-by-hour fixed effects, interconnection level. The pass criterion is their 95% CI. This tests the demand-regressor machinery, the time alignment and the EIA-930 handling, which AVERT cannot.
   - Cost: four more CAMPD quarters (2019) plus EIA-930 for 2019.
   - Confirm Holland's load source in the SI **[verify]**. If it is not EIA-930, note the difference.
   - This is the "reproduce a published number before extending" step the project's standing rules call for.
3. **Keep AVERT** as the check on the plumbing, with a tighter ±5% band after the basis corrections. Run both FD and levels against it.
4. **Add cross-dataset consistency checks** (pre-register thresholds):
   - Fraction of marginal demand met by fossil = β from regressing EIA-930 fossil generation on ΔD. Expect 0.6–1.05. Outside that range, stop.
   - Implied marginal heat rate = β_HI(CEMS) / β_fossilgen(EIA-930). Expect 6.5–11 MMBtu/MWh for gas; outside that range, stop.
   - CEMS coverage: annual CEMS CO2 by BA vs the EIA-930 CO2 estimate and eGRID BA CO2. Report it.
   - Placebo: ERCOT CEMS on ΔD_PJM, controlling for ΔD_ERCOT. Expect ≈ 0.

### MF6. Pre-register the decision rule and spec-specific expectations; fix the ERCOT expectation (item 8)

**Missing decision rules.** The plan does not yet state:
- which spec and year produce the headline SRMER (2025 alone? the 2024–25 pooled average?);
- what tie band applies (the main analysis uses 5%, widened by the Monte Carlo);
- what the post says when the specification envelope straddles an off-grid value.

All three must be fixed before computation.

**The ERCOT expectation probably sits too low.** I applied the project's own grid-side accounting to AVERT's 2023 rates. This is DERIVED arithmetic, using upstream CH4 0.44 kg/MMBtu at GWP 29.8, f = 0.093, CMM 0.199 and a 3% loss. The all-gas multiplier on combustion CO2 is (1 + 0.093 + 0.44·29.8/53.06)/0.97 = 1.38; for coal it is 1.10.

| Region | AVERT 2023 Uniform EE (kg CO2/MWh) | Busbar (×0.95, assumed loss) | CO2e on project basis | Pre-registered |
|---|---|---|---|---|
| Texas | 587 | 557 | 770 (all gas); 811 without deflating | 600–720 |
| Mid-Atlantic | 618 | 587 | 761 (assuming 70/30 gas/coal by CO2) | 700–850 |
| US | 648 | 616 | 798 (same assumption) | 650–800 |

The demand-regressor spec will come in lower than AVERT's fossil-load basis, and 2024–25 ERCOT has more solar and storage than 2023. The 600–720 range may therefore be right for one spec and wrong for another.

Required changes:
- Write the expectations spec by spec: demand regressor vs fossil-load.
- Show the combustion-only to CO2e arithmetic, as above.
- Pre-register the post's wording for the case that is now plausible: **engines and turbines below the short-run marginal ERCOT grid.** The draft interpretation ("roughly a tie") must not be pre-committed.

---

## SHOULD-FIX

### SF1. First differences vs levels, and the flat-load estimand (item 1)

**Estimand.** A flat load δ added to every hour changes annual emissions by Σ_t (∂E_t/∂D_t)·δ. The flat-load MER is therefore the unweighted mean over hours of the hourly marginal rate, plus any intertemporal effects (SF2).

**Equal weighting of the 96 bins** is the right outer step, since the bins hold nearly equal numbers of hours. The problem is the inside of each bin:
- OLS gives β_b = Σ w_t β_t with w_t ∝ ΔD_t². With heterogeneous marginal rates inside a bin, this over-weights big-ramp days: weather extremes, peakers and occasionally oil.
- In bins where ΔD has small variance (overnight hours 2–4, the midday plateau), β_b is imprecise. Equal weighting gives those noisy slopes full weight.
- The plan's specification has no bin intercept, so the systematic ramp, with its start-up heat input, also drives identification.

**First differences vs levels.**
- First differences remove slow confounders such as fuel prices, outages and fleet changes. But they emphasize fast-responding resources (CTs, storage, imports, hydro) and raise the ratio of measurement noise to signal, which attenuates β (see SF4).
- A sustained flat load is "slow". In PJM, coal units with ramp constraints respond to persistent shifts more than to hour-to-hour fluctuations. First differences may therefore understate the coal share.
- Holland-style levels with month × hour fixed effects identify the response from day-to-day level variation within a cell. That is closer to "D is δ higher all day", but more exposed to within-month confounders, which the wind/solar controls (MF2) partly address.

**Recommendation.** Pre-register a small specification set and name one primary:
- (i) Levels, CO2_t = β·D_t + γ'RE_t + month × hour fixed effects (Holland); and as a variant with β by season × hour.
- (ii) First differences with season × hour bins and bin intercepts (Siler-Evans).
- (iii) 24-hour differences, Y_t − Y_{t−24} on D_t − D_{t−24}, by season × hour. This keeps the confounder removal of differencing but identifies from day-to-day level shifts at the same clock hour, which matches the flat-load thought experiment best.
- (iv) Daily totals: ΔE_day on ΔD_day, with month and day-of-week fixed effects. This is the cleanest "flat block" estimator, and it also handles SF2.

I would make (i) or (iii) primary, with (ii) and (iv) as the main robustness checks.

**Precision weighting.** Report per-bin var(ΔD) and β_b standard errors. If any bin's SE exceeds about 25% of β_b, smooth β across adjacent hours within a season (a cyclic spline in hour). Alternatively, bin on net-load deciles × season instead of clock hour; the marginal unit is a function of system state, which is how AVERT bins. Then integrate over the empirical distribution of hours.

**The plan's sensitivity 2** (pooled, no bins) is a ramp-variance-weighted number, not a flat-load check. Label it as such.

**Size of the increment.** Data-center additions are GW scale, a few percent of PJM peak. Evaluate β(state) at D and at D + δ to check that the linear approximation holds.

### SF2. Storage, pumped hydro and hydro response counted as zero-emission

The contemporaneous hourly regression treats any demand met by battery discharge, pumped storage (PJM has Bath County, about 3 GW **[verify capacity]**) or reservoir hydro as zero-emission. For a persistent flat load, that energy must be replaced: storage is recharged and hydro is shifted from another hour, at that hour's marginal rate. The hourly estimator therefore biases SRMER low. ERCOT's battery fleet grew sharply over 2024–25, so the bias is growing in the window being estimated.

The daily-total spec (SF1 iv) captures within-day shifting. Report the difference between it and the hourly specs as an explicit "intertemporal" term.

### SF3. CEMS data handling: unit-count discontinuities, substitute data, coverage, gross load (item 4)

**Unit-count discontinuities.** A unit-hour row missing from CAMPD creates a dip in the regional aggregate, which shows up as a +/− spike pair in first differences. A unit entering or retiring changes the aggregate smoothly and is not a problem. Missing rows, monitor outages and reporting gaps are.
- Count reporting units per region-hour and flag hours where the count departs from the rolling daily mode.
- For units that report in the hour before and after a gap, interpolate or drop that hour pair. Report the counts.

**Substitute data.** Part 75 substitute data, used during monitor outages, are often at maximum potential values, which produces heavy-tailed spikes. Use the measure-indicator columns in the bulk files **[verify column names]**. Run the analysis with and without unit-hours flagged as substitute. Report the share of CO2 that is substitute data.

**Operating time [verify].** CAMPD gross load is, I believe, MW averaged over operating time, while heat input and CO2 mass are hourly totals. MWh then equals gross load × operating time. This matters for sensitivity 1 and for all heat-rate checks. CO2 is reported in short tons: multiply by 907.185 to get kg.

**Coverage.**
- CEMS misses fossil units under 25 MW and generally reciprocating engines **[verify which RICE units report under Part 75]**.
- ERCOT has a meaningful fleet of RICE peakers. These are the same technology as the off-grid recips, with W-7 slip of 0.522 kg/MMBtu.
- So the grid's short-run margin probably includes some engine output that CEMS does not see, and the slip asymmetry favors the grid.
- Quantify with EIA-860 IC (internal-combustion) capacity and EIA-923 IC generation in ERCO and PJM. Then either scale up, or report the gap as a downward bias of known size.

**Gross vs net.** Diagnose the CEMS gross-load convention for combined-cycle plants: compare annual plant CEMS gross load with EIA-923 net generation. Some combined-cycle plants report output from the combustion turbines only. Flag plants with a ratio below 0.8 or above 1.15.

### SF4. EIA-930 anomalies and imputation (item 4)

Keeping imputed values "as published" is not neutral under first differences. Imputed hours are smooth interpolations that carry no information. Real spikes and dropouts in EIA-930 demand are classical measurement error in the regressor, which attenuates β, and differencing makes the attenuation worse.

**Which demand series.** The BALANCE files carry original and adjusted/imputed demand columns **[verify current column names]**. Use EIA's adjusted/imputed demand as the primary series.

**Drop rules.**
- For first differences, drop hour t if t or t−1 is imputed or flagged.
- Screen outliers with a rule in the style of Ruggles et al. 2020 (Sci. Data 7:155) **[verify citation]**, or drop |ΔD| greater than 5 × the bin median absolute deviation (MAD).
- Report the counts.

**Sensitivity.** Run it with flagged hours kept, as the plan does now.

**Lower-48 demand.** Use EIA's published US48 series and confirm that it equals the BA sum.

### SF5. Bootstrap and inference (item 2)

**The scheme.** The plan's scheme is reasonable. Specify it as follows:
- Resample 1-week blocks of the full hourly series.
- In each draw, re-estimate every bin's β and every fuel equation. The fuel equations must share the same blocks (see SF6).
- Recompute the flat-load mean and the CO2e assembly per draw. This preserves dependence across bins and fuels.

**Options.**
- A circular block bootstrap, or resampling calendar weeks stratified by season, avoids under-sampling the ends of the year and keeps the sample size of each season fixed. Either is a minor improvement over the moving block.
- Run a block-length sensitivity: 1 day, 1 week, 4 weeks.
- Add Newey-West HAC (Bartlett, 168 lags) as an analytic cross-check, which also matches Holland.

**Draws.** 1,000 is adequate for a 90% percentile CI. The Monte Carlo error on the 5th-percentile endpoint is small. The regressions run on aggregated region-hour series, so 2,000 to 5,000 draws are cheap; use 2,000 and fix the seed.

**The larger issue.** With about 8,760 to 17,520 hourly observations per region and a high R², the sampling CI will be a few kg/MWh. The CEDM values had ±1–2 kg/MWh. The variation across specifications (MF2, SF1, SF2) will be 10 to 30 times larger. A 90% CI bar on the dot plot would imply false precision.
- Plot the pre-registered specification envelope as the bar, with the bootstrap CI as an inner tick.
- Show 2024 and 2025 as separate markers. Year-to-year variation is the honest indicator of short-run drift.

### SF6. Fuel decomposition: assemble CO2e as one dependent variable, and check closure (item 3)

**Additivity.** Equation-by-equation OLS with identical regressors equals SUR, and OLS is linear. So Σ_f a_f·β_f equals the β of the composite Y = Σ_f a_f·Y_f exactly, provided the samples and weights are identical. The plan's assembly is therefore consistent, but only if:
- every equation uses the same rows (same drops and same outlier screen); and
- the bootstrap uses the same blocks across equations. Otherwise the CI ignores the covariance between fuel β's.

The simplest route is to construct Y_CO2e,t in levels first and run one regression per spec. Keep the per-fuel regressions only for reporting.

**Closure check.** β_CO2 against 53.06·β_gasHI + (coal EF)·β_coalHI + (oil EF)·β_oilHI will not close exactly, for three reasons:
- coal CO2 per MMBtu varies by rank, from about 93 to 98;
- some CEMS fuels fall outside gas/coal/oil: petroleum coke, wood, process gas, tire-derived fuel;
- CAMPD assigns fuel per unit (primary and secondary fuel), not per hour. Dual-fuel gas units burning oil in cold snaps, which are common in PJM in winter, are labelled gas. Coal units co-firing gas are labelled coal.

Pre-register a closure tolerance of 3%, and diagnose any miss.

**Fuel classification.** An improvement: classify each unit-hour by its CO2/heat-input ratio (about 53 for gas, about 73 for oil, about 93–98 for coal), so mixed-fuel hours are split approximately. That ensures upstream CH4 attaches only to gas-ratio heat input.

**Slip consistency.** Any RICE gas units that are in CEMS should carry the same W-7 slip as the off-grid recips, not Table C-2 combustion CH4.

### SF7. Cambium basis and weighting (item 7)

**Internal contradiction.** Line 65 says "end-use basis, so no extra loss term is applied". Line 68 says to convert to busbar and then apply 3%. Pick one.
- The workbook has one Distribution Loss Rate, 0.036, for every region, and the Levelized LRMER tab offers Location = Busbar.
- The two conversions, ×(1 − 0.036) then ÷(1 − 0.03), net to ×0.994, so the choice is numerically a wash (−0.6%).
- There is a conceptual question **[verify in the Cambium documentation]**: if ReEDS/PLEXOS busbar load already includes inter-regional transmission losses, the extra ÷0.97 double-counts. That would push the grid side up, against the post.
- Disclose whichever is chosen.

**Validation passed.** grid.py's linear interpolation between the 5-year points reproduces the workbook's own cached levelized output to four decimals: Mid-case, combustion CO2, start 2025, 20 years, 3% discount, end-use. CAISO 99.452, ERCOT 158.637 and FRCC 245.306 all match the workbook. Record this as V-M2 in METHODS.

**Discounting.** Cambium's default is a 3% real discount rate. The plan's 0% simple mean gives a lower LRMER, because the LRMER falls over time. Mid-case 2027–2046 CO2e:

| Region | 0% | 3% |
|---|---|---|
| ERCOT | 147.2 | 159.0 |
| PJM_East | 271.6 | 279.4 |
| PJM_West | 198.0 | 209.4 |

The project rule is to be conservative toward the claim under critique. The low LRMER favors the grid, which favors the post's claim, so report the 3% value as primary or show it alongside.

**PJM East/West weights** are not specified in the plan. Use the same method as for the US.

**US weights.** EIA-861 state retail sales allocated to GEA regions by county population share is acceptable but indirect. Options:
- Cambium's own projected end-use load by GEA per year, from the Scenario Viewer if it can be reached. This is internally consistent with how the LRMER was computed.
- A weighting by data-center capacity (Cleanview project locations), as a sensitivity. The relevant weights are where the new load goes, not where today's load is.
- Equal weighting, as the plan already has.

**Order of operations.** Do the matched-L replacement (MF1) per GEA and year before weighting and averaging. Everything is linear, so the order only matters for keeping it auditable.

### SF8. Build margins (item 6)

**Partial-year units.** The newest units dominate the Tool 07 sample by construction, so capacity-factor imputation for partial-year units would carry most of its weight. Instead:
- Define the sample on units with a commercial operation date (COD) on or before December of year−1, so that year has a full year of generation for each.
- Or use each unit's first full 12 months from EIA-923 monthly data.
- Treat imputation with region × technology capacity factors as a sensitivity, not the primary. Write the rule down before running, e.g. units with fewer than 6 months use the fleet CF.

**Heat rates.**
- EIA-923 fuel and generation are at plant × prime mover × fuel level, not generator level.
- Combined-cycle heat rates must combine CT + CA + CS: the steam part reports generation with no fuel.
- At plants with mixed vintages, a new CT shares the prime-mover bucket with old CTs. Use only plants where every unit of that prime mover is in the sample. Otherwise fall back to the EIA-860 or vendor heat rate, or to the fleet heat rate for new units of that prime mover.
- First-year heat rates include commissioning and testing. Use the first full calendar year.
- IC units need W-7 slip in `em.intensity()`. CTs and CCs get 0.004, as in `cases.py`.

**The Tool 07 20% rule.**
- The plan's sample wording matches the Verra M0325 paraphrase of Tool 07 steps (a)–(c). Steps (d)–(f) (capacity additions and age limits) are unread. The original v7.0 text and its default wOM/wBM weights must be verified from the primary PDF, for example with the Chrome tool, or from a peer-reviewed source that quotes it verbatim, before anything is labelled "Tool 07". Do not fill in from memory.
- The Verra point that wOM = 1 for projects increasing grid consumption has to be resolved before the write-up, not after.

**Foreseeable result for PJM (DERIVED, rough).** PJM net generation is about 800 TWh/yr **[verify]**, so 20% is about 160 TWh. The newest units summing to that probably reach back to the 2015–2020 combined-cycle wave. The PJM recent BM could then be about 350 kg CO2/MWh combustion, which is about 470–500 CO2e on the project's basis. That is above SOFC (460) and on-site CC (475), and well above the pre-registered "100–250". Revise the expectations or split them by region. The fixed 2021–2025 window will be much cleaner.

**Combined margin.** Tool 07's operating margin (OM) is a fossil-weighted average or a dispatch-data OM, not a regression SRMER. Either compute a Tool 07 OM, or relabel "CM = 0.5·SRMER + 0.5·BM" as an ad hoc blend, not a CDM combined margin.

**Annual energy matching.** Matching a 60%-solar BM to a flat load is physically inconsistent. Add an hourly-matched variant as a sensitivity: serve each hour from the BM's generation profile and fill the shortfall at the hourly SRMER.

**M4.** Planned retirements are ignored. That is defensible for "what is being built", but note it.

### SF9. ERCOT flexible-load endogeneity

ERCOT's large flexible loads (crypto, Controllable Load Resources) curtail at scarcity prices and during 4CP (four coincident peak) intervals. ERCOT demand is therefore partly endogenous to supply conditions in exactly the hours when peakers are marginal, which attenuates β at the top of the load distribution. Data centers may also curtail at 4CP, so a flat profile is not exact either.
- Note this as a caveat.
- Optionally run an IV using population-weighted temperature (CDD/HDD), with wind/solar controls.
- Optionally run a data-center-profile weighting that removes 4CP hours.

---

## OPTIONAL

- **Horizon mismatch.** The SRMER is estimated from 2024–25 data but applied to plants operating from 2027. State this. Use the ERCOT 2024-vs-2025 trend as a rough indicator of drift.
- **Marginal T&D losses.** If marginal losses (6%) are argued for the SRMER, apply the same logic to every marginal metric (LRMER and BM), not only the SRMER.
- **Latent issue in the main analysis (flag only).** Cambium says its 2.2% is Alvarez's rate excluding local distribution. That is about 2.3% × (1 − ~3.4% distribution share). The main analysis applies the whole-chain 2.3%, including local distribution, to transmission-connected plants on both sides. Because the off-grid options burn more gas, this widens the gap by roughly 2 kg/MWh for recips (rough arithmetic: 3.4% of a ~110 kg upstream term on the off-grid side minus ~1.5 kg on the grid side). It does not change any verdict.
- **Reproducibility.**
  - Record CAMPD bulk-file names, download dates, sizes and SHA-256 hashes; CAMPD data are resubmitted and revised. Do the same for the EIA-930 snapshot.
  - Save the unit→BA crosswalk, the plant time-zone table, a per-unit coverage and substitute-data table, and the bootstrap seed under `data/marginal/`. These are small and make it possible to regenerate everything without re-downloading.
  - Report the share of CEMS CO2 left unmapped after the eGRID2023 → EIA-860 2024 → EIA-860M fallback.
- **Disk.** Eight quarterly files for 2024–25, plus four for the 2023 validation and four for a 2019 Holland reproduction, means 16 streamed files. Streaming one at a time keeps this within the project's disk rule. Check the CAMPD file sizes before committing.

---

## Suggested pre-registered robustness set (to freeze in PLAN_marginal §M1)

| # | Dimension | Primary | Variants |
|---|---|---|---|
| R1 | Estimator | Levels + month × hour fixed effects, or 24-hour differences (pick one) | First differences with season × hour bins and intercepts; daily totals; pooled single β (labelled as ramp-weighted) |
| R2 | Renewables | ΔD with ΔWind and ΔSolar controls | No controls; net-load regressor; ERCOT available-capacity control if obtainable |
| R3 | System boundary | ERCOT: own CEMS. PJM: EI CEMS on ΔD_PJM with ΔD_rest-of-EI. US: load-weighted mean of interconnections | PJM own-Y; pooled lower-48 |
| R4 | Cleaning | Drop imputed/flagged hours (t, t−1) and substitute-data unit-hours; screen ΔD at 5 × MAD | Keep everything as published |
| R5 | Bins | Season × hour, smoothed if SE/β > 25% | Net-load deciles × season |
| R6 | Year | 2025 | 2024; pooled |
| R7 | Coverage | As measured | Scaled for non-CEMS fossil (IC and units under 25 MW) |
| R8 | Inference | Weekly block bootstrap, 2,000 draws, fixed seed | 1-day and 4-week blocks; Newey-West with 168 lags |
| R9 | Losses | 3% | 6% (marginal) |
| R10 | Cambium | Calibrated matched-L replacement, 3% discount | Unadjusted; 0% discount; plan's formula (for transparency) |
| D1 | Diagnostics, must pass | Lag-0 cross-correlation peak; Holland 2019 reproduction within their 95% CI; AVERT ±5% after basis corrections; fuel closure ±3%; fossil share 0.6–1.05; marginal gas heat rate 6.5–11 | — |
| D2 | Decision | Headline = primary spec. The figure bar is the R1–R4 envelope. Verdict vs each off-grid option uses tie band = max(5%, envelope half-width) | — |
