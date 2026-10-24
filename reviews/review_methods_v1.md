# Methods review of PLAN.md v1.1 (quantitative methods, uncertainty, metrics, FaIR)

Reviewer: methods/uncertainty reviewer (Claude subagent), 2026-10-24. PLAN.md not edited.
Arithmetic was run in a throwaway script (session scratchpad `/private/tmp/claude-501/-Users-hausfath-Desktop-Climate-Science-The-Climate-Brink/b6426cdf-39dc-4a8b-80be-b965c2c3cd9b/scratchpad/check.py`, python3.13; not kept in the project). The numbers below come from that script. Inputs read from saved sources:
transcript (`sources/latitude_catalyst_irzak.txt`), eGRID2023 rev2 summary tables (`sources/lit_scan/egrid2023_summary_tables_rev2.xlsx`),
`sources/lit_scan/FINDINGS.md`, and the installed FaIR 2.2.2 source. Anything marked **[verify]** was not checked against a primary source here.

## Bottom line

The plan is well structured and its §7 arithmetic is right (recip 0.964 kg CH4/MMBtu → 28.7 kg CO2e/MMBtu, 35% of recip GWP100 total, 20% for NGCC). Four problems
need fixing before anything runs:

1. The V1 pass threshold can't detect errors in the methane term, and the §3 function has no upstream-CO2 term, so V1 will probably fail for a real reason.
2. The ranking test (§7) is aimed at the wrong prime mover. The test only has something to decide for NGCC (and probably SOFC), where BTM and the grid
   are tied on CO2 alone in ERCOT. A tie means the result rests on a sign test over a ~2 kg difference.
3. "Max of average and LRMER" is a robustness criterion, not a reference line. It also makes the decomposition depend on order.
4. FaIR 2.2.2 does not oxidize fossil CH4 to CO2, so the FaIR runs are inconsistent with the 29.8 GWP the rest of the plan uses.
   Its default `ch4_method` is also not the one the v1.4 calibration uses.

V2 (Frost) has a much cleaner identification than the plan proposes. It reverses the plan's conclusion that her implied upstream and facility leakage exceeds her stated 4%.

---

## MUST-FIX

### M1. Recast the ranking test as break-even leakage L* and pre-register region-specific predictions (answers Q2)

Combustion CO2 alone, at plan heat rates (EF 53.06 kg/MMBtu):

| Option | HR (HHV) | CO2 kg/MWh | + CH4 at W-7 slip, L = 2.43%, GWP 29.8 | Total |
|---|---|---|---|---|
| Recip 4SLB | 8.4 | 445.7 | 241.4 | 687.1 |
| Simple cycle | 10.0 | 530.6 | 133.0 | 663.6 |
| NGCC | 6.6 | 350.2 | 87.8 | 438.0 |
| NGCC | 6.4 | 339.6 | 85.1 | 424.7 |

Grid, eGRID2023 total-output CO2e (combustion only) ÷ (1 − 0.042 eGRID grid gross loss), plus upstream CH4 on grid gas fuel (gas share × 7.781 MMBtu/MWh, EIA 2025 fleet operating HR):

| Region | Combustion only (kg/MWh) | Delivered, L = 0 | Delivered, L = 2.43% | Grid gas fuel (MMBtu/MWh) |
|---|---|---|---|---|
| ERCT | 334.1 | 348.8 | 401.9 | 3.86 |
| US | 349.7 | 365.0 | 411.2 | 3.36 |
| RFCE | 271.8 | 283.7 | 341.6 | 4.21 |
| RFCW | 415.5 | 433.7 | 474.2 | 2.94 |

What follows from these tables:
- **Recips and simple cycle:** CO2 alone (446, 531) is above every regional average (284–434 delivered). Methane can only widen the gap. For recips the §7
  test settles before any methane data is used. The plan already anticipates this; the point is that it holds in every region checked, not only ERCOT/PJM.
- **Structural result:** BTM burns more gas per MWh (6.4–10 MMBtu) than the grid does (2.9–4.2 MMBtu per grid MWh). At matched L, adding methane
  therefore moves every BTM option further toward "worse than grid", and the ranking can only flip one way. The question is never "can methane make BTM look
  better"; it is "is BTM below the grid on CO2, and if so, at what L does that stop".
- **NGCC is the knife edge.** NGCC at 6.6 vs ERCT on CO2 alone: 350.2 + 0.8 (turbine slip) vs 348.8, a 0.6% difference.
  The plan's binary test would label this "methane widens, doesn't create" on the strength of a 2 kg/MWh difference, which is well inside heat-rate
  uncertainty. That is the gameability problem: the outcome flips on HR choices of ±3%.
- Break-even matched L* for BTM NGCC (L where BTM = grid; "none" = BTM above grid at every L):

| Region | NGCC 6.4 | NGCC 6.6 | NGCC 7.0 | NGCC 7.5 |
|---|---|---|---|---|
| ERCT | 0.67% | none | none | none |
| US | 1.59% | 0.85% | none | none |
| RFCE | none | none | none | none |
| RFCW | 5.03% | 4.24% | 2.87% | 1.47% |

  "PJM" spans RFCE and RFCW, which give opposite answers, so the regional definition decides the result (see S5).

Recommendations:
- (a) Make the **primary output L\*** (and the analogous break-even slip for recips under part load) for each prime mover × region × reference. It needs no
  distribution, it is horizon-explicit, and it maps directly to "no recips / no high-leak gas" policy statements.
- (b) Add a **tie band**. If |BTM − grid| on CO2 alone is under ~5% (about the combined HR, EF and grid-factor uncertainty), record "tied on CO2", not "above" or "below".
- (c) **Pre-specify the primary cells** before running: GWP100, matched L = 2.43%, eGRID average, regions ERCT and US, plus a named PJM definition.
  The prediction to record now: recip and SC above in all cells, already on CO2. NGCC tied on CO2 in ERCT and US, above with methane. NGCC below in RFCW.
  Everything else is labeled sensitivity. With roughly 5 movers × 5 L × 3 references × 3 regions × 2 metrics ≈ 450 cells, some cell will "flip" by chance
  unless the primary cells are fixed in advance.
- (d) **Promote SOFC (Bloom) from optional to primary.** FINDINGS gives Bloom 14% of the identified BTM MW (Stargate Jupiter alone is 2.45 GW). At HR 6.5–7.5
  it sits on the same knife edge as NGCC. In contrast, BTM NGCC is rare in the operating and planned fleet (mostly aeroderivatives, recips and Bloom). Without SOFC,
  the one live ranking question would rest on a configuration that is uncommon in practice. Consider a "Cleanview-weighted BTM mix" case as the headline bar.
- (e) **The §7 "Interesting/narrowing" outcome is not mutually exclusive with the other two.** Replace the three bullets with an exhaustive decision table:
  {CO2-only: above / tied / below} × {full: above / tied / below} for each primary cell.

### M2. Make the decomposition symmetric and fix the reference before decomposing (Q2, Q5)

- The "CO2 alone" state must strip methane from **both** sides at once: BTM combustion CO2 vs grid combustion CO2e (eGRID, no upstream), with T&D applied
  in both states. If methane is added to BTM first and the grid second, the intermediate state is a straw man. Done simultaneously, the sign test
  does not depend on order.
- The additive gap decomposition Δ = ΔCO2 + ΔCH4 (+ΔN2O) is exact and order-free, because E is linear in the GWP-weighted terms at fixed HR. Order
  dependence enters through three nonlinearities, which need explicit handling:
  1. `max(avg, LRMER)` can switch identity between the CO2-only and full states. Choose the reference from the full metric and hold it fixed, or report both references separately (preferred).
  2. In part-load cases, HR × slip interact multiplicatively. Use a Shapley (average over both orders) split if part-load effects are decomposed.
  3. Report the gap both as an absolute (kg/MWh) and as a ratio. Methane can widen one and narrow the other. Pre-register the absolute gap as primary.

### M3. V1 validation: the threshold can't see the methane term, and the function is missing upstream CO2 (Q6)

- At NETL's 0.55% (kg CH4 per kg NG delivered) and about 20.2 kg NG/MMBtu (composition **[verify]**), upstream CH4 ≈ 0.0055 × 20.2 × HR(≈6.37 **[verify NETL HR]**) × 29.8
  ≈ **21 kg CO2e/MWh**, about 5% of 394.7. A ±3% total tolerance (±11.8 kg) allows a **~56% error in the CH4 term**, and the CH4 term is the quantity
  under study. A GWP mismatch (27.0 vs 29.8 = 2 kg) or a basis error in L would pass undetected.
- Residual check: NGCC 394.7 − 338 (combustion at 6.37) − 21 (CH4) ≈ **36 kg/MWh unexplained**. For the peaker, 34.5% HHV → 9.890 MMBtu/MWh → 524.8 kg CO2. With
  CH4 ≈ 0.0055 × 20.2 × 9.89 × 29.8 ≈ 33 kg, **~102 kg/MWh is unexplained**. NETL LCA totals typically include upstream CO2 (compressor and processing fuel
  combustion, acid-gas venting, flaring) and possibly construction and T&S terms **[verify against NETL stage table]**. The §3 function has no upstream-CO2 term,
  so V1 will fail, and it will fail for a real reason. The peaker residual per MMBtu (~10 kg) is about twice the NGCC residual (~5.7 kg), which suggests the two NETL cases
  differ in basis (leak, GWP, or boundary). Diagnose this before using the peaker as a check.
- Fix:
  - (i) Add an explicit `m_upCO2` term (kg CO2/MMBtu delivered, from NETL's upstream stage breakdown). Omitting it favours BTM, because BTM burns more gas per MWh,
    so it is "conservative", but it breaks V1 and it understates both sides.
  - (ii) Validate **component by component**: combustion CO2 to ≤1%, upstream CH4 to ≤10% (or ≤2 kg/MWh), upstream CO2 to ≤10%, total to ≤2%. Use NETL's own GWP, composition and leak
    definition.
  - (iii) Write out the conversion from NETL's "kg CH4/kg NG delivered" to the plan's L (CH4 lost / CH4 produced). A deterministic replication with the source's own
    inputs should land within rounding (<1%), so a 3% miss is itself a finding.

### M4. FaIR configuration: oxidation, CH4 method, stochasticity (Q4)

Checked in the installed FaIR 2.2.2 source:
- **No CH4 → CO2 oxidation.** `oxidation_matrix` is commented out in `fair/fair.py` (lines ~1293, ~1344). AR6's fossil GWP100 of 29.8 vs 27.0 non-fossil is that
  oxidation CO2 (AR6 Table 7.15 **[verify values]**). As planned, the FaIR runs correspond to 27.0 and the CO2e bars to 29.8, so the two products disagree
  by about 10% on the CH4 term. **Fix:** add 44.01/16.04 = 2.74 kg CO2 per kg CH4 to the CO2 perturbation, lagged by the CH4 perturbation lifetime (≈12 yr e-folding). Or report
  CO2e bars at 27.0 as the FaIR-consistent variant.
- **CH4 lifetime method.** The `FAIR()` default is `ch4_method="leach2021"`. The v1.4 calibration was built with `thornhill2021` (lifetime dependent on CH4, N2O,
  VOC, NOx, temperature) **[verify in the fair-calibrate config]**. Pass it explicitly, or the CH4 lifetime feedback and the calibrated parameters will not match.
- **Stochastic forcing.** `climate_configs["stochastic_run"]` defaults to False in 2.2.2. Check whether the v1.4 parameter CSV or the example workflow switches it
  on, and keep it off. If it is on, identical seeds in the paired runs are mandatory. Run an A − A zero test, which must return exactly 0.
- **Correct the "1e-6 K is inside numerical noise" statement.** A deterministic float64 run resolves 1e-6 K differences easily. Fleet scale is still a good
  choice (linear regime, interpretable), but the justification should be size: recip fleet ≈ 2.4 Mt CH4/yr (300 TWh × 8.4 × 0.964) and ≈ 134 Mt CO2/yr. That is under 1%
  of anthropogenic CH4 and ~0.3% of CO2, well inside the linear range.

---

## SHOULD-FIX

### S1. Uncertainty: scenarios vs parameters; no single P(BTM > grid) (Q1)

Classify the inputs before deciding on Monte Carlo:

| Genuinely uncertain, has a defensible distribution | Scenario / choice (no distribution) |
|---|---|
| EF_CO2 (±1%), c_CH4 of pipeline gas (0.884–0.970 mass frac), full-load HR for a given model (±3%), full-load 4SLB slip across engines (FINDINGS: ~1.3–3.5%; Vaughn 2021 mean CI), regional L structural spread (Permian 2.1–3.7% across methods 2019–2024; Sherwin six-region 2.27–2.59% is a sampling CI only), AR6 GWP ranges | prime mover; operating regime (part load, N+1 spinning, startups); gas sourcing (basin, certified); grid reference concept (avg / LRMER / SRMER); grid year and trajectory; metric and horizon; facility leaks (no data); part-load slip premium (no data) |

- Do **not** report a single marginal P(BTM > grid) integrated over scenario choices. That would put a probability on the author's own choices and give false
  precision. Any MC result should be conditional on a scenario cell and labeled "under stated distributions".
- A within-cell MC is cheap and worth doing to size the tie band (M1b). The key requirement is **correlated sampling**: L must be drawn once and applied to
  BTM and grid together (matched supply), and GWP draws apply to every CH4 term at once. Independent draws would inflate the spread of the difference.
- Variables with no distribution (part-load slip, facility leaks) belong in break-even form: "BTM NGCC exceeds ERCT average if facility leaks exceed X%". They should
  not be given invented uniform priors.
- A tornado plot of the primary NGCC and SOFC cells shows what drives the ranking better than a probability would.

### S2. Grid upstream L: one national line is not uniformly conservative (answers the §5 reviewer question)

A fixed grid line at L = 2.43% is conservative toward BTM only when the BTM case has L < 2.43%. For the Permian BTM cases (4% and the tail) it penalizes BTM
relative to a grid that, in ERCOT, also burns largely Texas and Permian gas. Recommendations:
- **Primary:** matched L. This is the consequential view, where the incremental MWh, whether BTM or grid, draws on the same marginal supply. It is also the view under which L* (M1) means something.
- **Labeled scenario:** "BTM buys certified low-leak gas, grid does not" (BTM at low L vs grid at 2.43%).
- Describe Sherwin 2.43% as a **six-region weighted average of covered production**, not a national measurement (FINDINGS §4).
- **Data error:** the plan labels 0.2% as "MiQ A". MiQ grade A is ≤0.05%, and 0.2% is the grade C ceiling (FINDINGS, MiQ Table 2). MiQ is upstream-facility only, on a
  sales-gas denominator. A certified-gas buyer still carries gathering, processing and transmission losses, so "MiQ A" is not a valid whole-chain L. Build the low case as
  MiQ upstream plus a gathering/processing/transmission adder **[source needed]**.
- **Basis conversions:** Alvarez, Zhang, Chen and Sherwin use % of gross or covered production. MiQ and MethaneSAT use sales gas. NETL uses kg CH4/kg NG delivered. The plan's
  `c·L/(1−L)` assumes everything not leaked is delivered, which ignores lease and plant fuel and NGL removal (a few % relative). Put a conversion table in METHODS.md.
- Coal mine methane on the grid side is also conservative toward BTM. Rough order: ~1.5–2 kg CH4 per coal MWh ≈ 50 kg CO2e per coal MWh × 12.7% coal (ERCT) ≈ 6 kg/MWh
  **[rough, verify against GHGI]**. That is small but it belongs in the same accounting as upstream gas.

### S3. Max(avg, LRMER) (Q5)

The two quantities answer different questions. An average rate is attributional ("your share of the grid's emissions"). LRMER is consequential ("emissions
caused by adding this load, including induced build-out"). Adding a large new load is a consequential question, so **LRMER is the matched estimand** and the average is context.
Taking a per-region max gives a reference whose definition changes by region and is chosen after the fact, and its time bases differ (eGRID 2023 static vs
Cambium 2027-start levelized). It is coherent only as a **robustness criterion**: "BTM exceeds the grid under both accounting views". Present it as a two-condition
check with both lines drawn, not as one "reference line".

Further points:
- **Same view on both sides.** The BTM side uses attributional supply-chain L. The Permian is oil-driven, so marginal gas demand may be met by Haynesville dry gas
  (no verified L, per FINDINGS) rather than by more Permian associated gas. If LRMER is the grid estimand, the matching BTM L is the marginal-supply L.
  State this caveat explicitly.
- **Cambium 2024 vintage.** The workbook (submitted Apr 2025) predates the July 2025 credit phase-outs, so its mid-case probably assumes IRA-era build and a
  low LRMER **[verify scenario assumptions]**. Conservative toward BTM means a higher grid, so use a no-IRA or high-RE-cost Cambium scenario if one exists, or flag that the LRMER
  likely understates. Also check whether Cambium values are busbar or end-use **[verify]**, and don't add T&D to end-use rates.
- **T&D.** Use eGRID's own 4.2% grid gross loss (Table 1), not "~5%". A transmission-connected data center avoids most distribution losses, so 4.2% overstates
  the loss it actually incurs. Keep it as the conservative choice, label it, and run transmission-only (~2% **[verify]**) as a sensitivity. BTM should also carry on-site MV losses and parasitics.
- **SRMER.** Use Cambium SRMER or EPA AVERT, not eGRID non-baseload. EPA does not present non-baseload as a marginal rate **[verify eGRID guidance wording]**, and
  at 1248–1379 lb/MWh it would inflate the grid line more than any other choice.
- **Grid trajectory.** Holding the grid constant for 2027–2046 while BTM is constant is conservative toward BTM. That is fine as primary, but state it, and run a
  declining-grid sensitivity (Cambium yearly path). This choice probably moves the FaIR ratio more than anything else in §6.

### S4. Frost V2: a sharper identification that reverses the plan's decomposition (Q3)

Arithmetic check of the plan (AR5 28/84, EF 53.06, r = 724/380 = 1.9053): x = 53.06(r − 1)/(84 − 28r) = **1.567 kg CH4/MMBtu** ✓. CH4 share at GWP100 = 45.3% ✓.
E = 380e9/(53.06 + 28·1.567) = 3.920e9 MMBtu. CF × HR over 18 months (50 GW × 13,149 h) = **5.96** ✓.

Alternative GWP sets (same method):

| Set | x (kg/MMBtu) | CH4 share @100 | Inside her 40–50%? |
|---|---|---|---|
| AR5 28/84 | 1.567 | 45.3% | yes |
| AR5 with cc feedback 34/86 | 2.263 | 59.2% | no |
| AR6 fossil 29.8/82.5 | 1.867 | 51.2% | marginal |
| AR6 non-fossil 27.0/79.7 | 1.700 | 46.4% | yes |
| AR4 25/72 | 1.971 | 48.2% | yes |

The share window cannot identify the GWP set: AR4 and AR6 non-fossil both fit, and 51% vs a spoken "40–50" is not a meaningful exclusion. The evidence for AR5 is that she
**states 28/84 verbatim** (transcript: "28 times more potent than CO2 over the 100-year terms, and 84 times more potent over the 20-year terms"). Cite that, and drop the
inference from the share.

**Rounding:** with 380 in 375–385 and 724 in 720–728, x ranges from 1.46 to 1.69 (±7%). The identification is reasonably robust to rounding of the totals.

**Better identification, a mass balance on the produced basis.** Suppose 7.5% = CH4 emitted / CH4 produced across the whole chain, the gas is pure CH4, and all non-emitted CH4 is
burned (2.744 kg CO2/kg CH4). Then the ratio is (2.744·0.925 + 84·0.075)/(2.744·0.925 + 28·0.075) = **1.9057 vs 1.9053 observed**. Solving for f gives
**f = 7.494%** (7.46–7.53% for 380 ± 0.5), and the GWP100 CH4 share is 45.3%. Her numbers reproduce to four figures under this reading, with nothing else assumed.
Consequences:
- The plan's "7.5% maps to ~8–9% of delivered CH4" comes from the plan's own 95%-CH4 delivered basis, not from anything Frost said. Retract it.
- Decomposition on the produced basis: 7.5% ≈ 4% (wellhead + gathering, as she states) + ~2.8–2.9% slip + **~0.6% facility**, which fits her "optimistic
  assumptions on facility leaks". The plan's conclusion that the parts she didn't state imply 5.9% upstream + facility (vs her 4%) does not hold.
- **The duration is ambiguous, not necessarily wrong.** "380 Mt ... in the next 18 months for those 50 gigawatts to come online" can be read as 18 months of
  operation (CF × HR ≈ 6.06 MMBtu/MWh on this basis, e.g. CF 0.71 at HR 8.5) or as an annual rate for capacity coming online within 18 months
  (CF 1.0 at HR ≈ 9.1, or CF 0.9 at HR ≈ 10, plausible for a recip/SC mix). The total pins CF × HR × duration, not CF × HR. Report both readings, and don't
  write that she "treats 50 GW as running for the full 18 months" unless she confirms.
- Suggest emailing Frost for the spreadsheet. A one-line confirmation beats any inference.

### S5. Region mapping

eGRID2023 summary tables have subregions, not BAs (FINDINGS §6). "PJM" is not one subregion, and RFCE vs RFCW give opposite NGCC answers (M1). Either build
PJM from the plant file aggregated by BA, or report RFCE and RFCW separately and say which one a given campus sits in. Align the Cambium GEA regions with the eGRID
regions. For grid gas fuel per MWh, use eGRID plant-file heat input by fuel, not gas share × fleet HR as done in this review (that was a check, not a method).

### S6. Slip central value and part-load treatment

W-7's 0.522 kg/MMBtu (~2.9% of CH4) sits at the upper end of FINDINGS' measured range (~1.3–3.5%; Vaughn 2021 found 4SLB compressors about 8% below AP-42).
Conservative toward BTM argues for a lower central slip (~2%) with W-7 as a sensitivity, or at least an explicit statement. This **does not affect the ranking**,
since recips are above every grid on CO2 alone, so it is low stakes. Turbines also have part-load and startup CH4 (Hajny 2019: 440 g/MMBtu during startup), and
aeroderivative HR rises steeply at part load. Apply the redundancy/part-load case to SC as well as recips.

### S7. FaIR design details (Q4)

- **Background dependence.** CH4 forcing follows roughly √[CH4] and its lifetime depends on background CH4, NOx and VOC. Marginal CO2 warming depends on the
  airborne fraction. Bracket with a low and a high background (SSP1-2.6 / SSP3-7.0, or CMIP7 L / H), not SSP2-4.5 alone. The BTM/grid ratio will be less sensitive than the absolute ΔT, so show both.
- **Report the per-member ratio** (BTM ΔT / grid ΔT computed member by member, then quantiles), not the ratio of medians. ECS and TCR spread largely cancels in the
  ratio. CH4 lifetime, forcing scaling, and carbon-cycle feedback spread do not, and they are the uncertainty that matters. Also report the per-member **difference**
  (BTM − grid ΔT): the ratio is unstable if the grid line is small (e.g., a low LRMER).
- **Overclaim.** "This replaces any argument about GWP20 vs GWP100" relocates the horizon choice to the reporting year (2035 / 2050 / 2100). It does not remove it.
  Show the full ratio time series, peak ΔT and its year, and a time-integrated ΔT. Say plainly that 2100 for a 2027–2046 step is CO2-dominated by construction.
- **Run CH4 emissions-driven** in the paired runs, and confirm that the calibrated ensemble's CH4 is not concentration-driven.
- **Add a FaIR validation (V3)**, following the reproduce-a-published-number rule. Using the same background, run 1 Mt CH4 and 1 Mt CO2 pulses and compute the ratio of
  integrated ERF over 100 yr. Compare with AR6 GWP100 non-fossil 27.0 (no oxidation) and with GTP100 (~4.7 non-fossil) **[verify AR6 Table 7.15]**. Pass if within the AR6 range.

---

## OPTIONAL

### O1. AR6 AGTP convolution as a cross-check, not a replacement

Convolving the emission steps with the AR6 Ch7 SM impulse responses (AGTP for CO2 and CH4) is about 30 lines, transparent, and reproduces AR6 metrics by
construction. Use it to cross-check FaIR's median ΔT trajectories. GWP* adds a third metric with its own contested framing for new sources, and it brings no
information FaIR doesn't already have. I would not use it in a public post.

### O2. Report per TWh/yr and per GW

Per TWh/yr is the right normalizer. Also report per GW at the assumed CF, since that is the unit announcements use.

### O3. Fleet-weighted headline bar

Weight prime movers by Cleanview's identified equipment shares (with its caveat that only ~30% of MW has identified equipment). This keeps the headline
tied to what is actually being built rather than to the cleanest BTM configuration.

### O4. N2O and the T&D multiplier

Apply the T&D divisor to the grid's upstream CH4 term too (done in the tables above). Being explicit avoids a 4% inconsistency.

---

## Answers to the six questions, in brief

1. **Uncertainty:** keep the case grid. Make break-even L* (and break-even facility leak and part-load slip) the primary output. Run only within-cell, correlated MC to size the
   tie band. Never marginalize over scenario choices.
2. **§7:** not well defined as written. It needs simultaneous both-side stripping, a fixed reference, a tie band, pre-specified primary cells, and an exhaustive outcome
   table. Order is irrelevant for the linear decomposition but matters through `max()` and through part-load HR × slip interactions. The live cases are NGCC and SOFC, not recips.
3. **V2:** the plan's arithmetic is correct. A produced-basis mass balance reproduces 724/380 to 4 figures at f = 7.49%, which overturns the 8–9% "delivered" mapping and the
   5.9% vs 4% decomposition. The GWP set cannot be identified from the share window (AR4 and AR6 non-fossil also fit). Her verbatim 28/84 is the real evidence. The duration is ambiguous (18-month vs annual).
4. **FaIR:** add oxidation CO2 or report at 27.0. Set `ch4_method` explicitly. Keep stochastic off and run an A − A test. Bracket the background. Use per-member ratio and difference. Add a pulse validation.
   AGTP convolution is a good cross-check. GWP* is not needed.
5. **max(avg, LRMER):** incoherent as a single line, coherent as an "under both views" robustness test. LRMER is the matched estimand for new load. Match the supply
   view on the BTM side. Watch the Cambium vintage.
6. **V1:** ±3% total is too loose (it allows ~56% error in the CH4 term) and probably impossible to meet without an upstream-CO2 term (~36 kg/MWh unexplained for NGCC,
   ~102 for the peaker). Validate component by component.
