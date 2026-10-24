# Off-grid gas for data centers: per-MWh CO2e with methane (pre-analysis plan v2)

Source idea: brink-ideas PR #36 (approved 2026-10-24). v1.1 was reviewed by a domain reviewer and a methods reviewer:
`reviews/review_domain_v1.md` and `reviews/review_methods_v1.md`. The reviewed text is `reviews/PLAN_v1.1_as_reviewed.md`. This v2 takes in both
reviews and three decisions Zeke made on 2026-10-24:
- the ranking test is a two-condition test against the eGRID average and new grid NGCC;
- leak rates are whole-basin, unallocated, with oil/gas allocation as a caveat and sensitivity;
- Frost is not contacted.

**Frozen 2026-10-24, before any case results were computed.** Any change after this point goes in §11 with its reason.

## 1. Question and claim under test
Zeke's claim (24 Oct 2026): data centers that get built should connect to the grid, not run on behind-the-meter (BTM) gas. The question: per MWh
delivered to a data center, how do BTM gas options compare with the grid once engine methane slip and upstream leakage count? Does methane
change which option is worse, or only the size of the gap? The claim under test is Zeke's own, so any choice that is defensible either way is
resolved **in favor of BTM gas**, and the alternative is run as a sensitivity.

What arithmetic already establishes (both reviewers, plan v1.1 §7):
- Recips and simple-cycle turbines emit more combustion CO2 per MWh (≈445–530 kg) than any grid average in the regions considered. eGRID2023 averages are
  ERCOT 334, PJM 326 and US 350 kg CO2e/MWh. For these two options, methane can only widen the gap.
- BTM burns more gas per MWh (6.4–10 MMBtu) than the grid's gas share does (3.3–3.6 MMBtu per grid MWh). At matched leakage, adding methane therefore always
  pushes BTM toward "worse", so the ranking can only flip one way.

**The live question is the efficient BTM options (combined cycle and SOFC), which sit near the grid average on CO2 alone.**

## 2. Validation
- **V1 (done).** The bottom-up function reproduces NETL Rev1 (DOE/NETL-2025/4933) NGCC-F component by component:
  - Combustion CO2: 337.8 vs NETL 337.6 (50.3 g/MJ × 6.713 MJ/kWh).
  - Upstream CH4 term: 21.1 vs 21.0.
  - NETL's upstream total (7.8 g/MJ × 6.713 = 52.4 kg/MWh) **sets the upstream CO2 factor**: f = (52.4 − 21.0)/337.6 = 0.093 of combustion CO2.
  - Total: 393.6 vs 394.7 on the generated basis (−0.3%).

  Pass thresholds are ≤1% for combustion, ≤10% for CH4 and ≤2% for the total.

  **Not explained:** the NETL fleet peaker (659.7 generated, 34.5% HHV, 205 kg NG/MWh). Our function gives ~606–629, depending on which NETL fuel figure is used.
  The residual (5–8%) probably comes from the CF < 0.2 basis (start-ups, capital per MWh) [unverified]. The peaker is not used as a check, and this is stated.
- **V2: Frost consistency.** Primary reading (methods reviewer): 7.5% of *produced* CH4 is emitted across the whole chain, the gas is pure CH4, and all non-emitted CH4 is
  burned (2.744 kg CO2/kg CH4). Then (2.744·0.925 + 84·0.075)/(2.744·0.925 + 28·0.075) = 1.9057, against the observed 724/380 = 1.9053, and the solved loss is 7.49%.
  The GWP set is AR5 28/84 because Irzak states it verbatim; the CH4-share window cannot identify it. V2 reports:
  - both duration readings: 18 months of operation (CF × HR ≈ 6.0), or an annual rate (CF 1.0 at HR ≈ 9.1);
  - the slip vs upstream+facility split of the 7.5% as a **surface** over recip share × slip, not a single point, because the fleet is about 65% turbines;
  - the context that about 2 GW is operating, against 50 GW assumed.

  Never write "next 18 months" as Frost's emissions.
- **V3: FaIR metric check.** On an SSP2-4.5 background, run 1 Mt CH4 and 1 Mt CO2 pulses in 2030. Compute the 100-year integrated-ERF ratio and the 100-year temperature ratio.
  Pass if both fall within the AR6 ranges for GWP100 and GTP100. Compare against non-fossil CH4 values, because FaIR does not oxidize CH4.

## 3. Emissions function (per MWh net delivered to the data-center bus)
E = HR × [ EF_CO2 · (1 + f) + GWP_CH4 · ( m_slip + m_up + m_fac ) + GWP_N2O · m_N2O ] / (1 − loss)

| Term | Value | Source |
|---|---|---|
| HR | MMBtu **HHV** per MWh net. LHV vendor figures are multiplied by 1.108 | labelled per case |
| EF_CO2 | 53.06 kg/MMBtu | 40 CFR 98 Table C-1 |
| f (supply-chain CO2: processing, compressor fuel, flaring) | 0.093 | NETL Rev1 via V1 |
| m_slip | prime-mover slip, kg CH4/MMBtu | §4 |
| m_up | c_CH4 · L/(1 − L), with c_CH4 = 18.7 kg CH4/MMBtu (NETL 20.1 kg NG/MMBtu × 0.93; range 0.884–0.970) | |
| L | CH4 emitted / CH4 in gross production, whole chain through transmission | §5 |
| m_fac | on-site and lateral leaks | sensitivity and break-even only; no distribution |
| N2O | 1e-4 kg/MMBtu | 40 CFR 98 Table C-2 |
| loss | grid: transmission-only 3% (sensitivity 2%, and ~5% total per EIA); BTM: 1% on-site MV and parasitic | EIA / lookup |
| Coal (grid side) | combustion from eGRID; coal-mine CH4 per MMBtu of coal from the EPA GHGI | lookup |

METHODS.md will tabulate the basis conversions: Alvarez, Zhang and Sherwin use gross production; MiQ and MethaneSAT use sales gas; NETL uses kg CH4 per kg NG delivered.
Lease and plant fuel and NGL removal (a few percent, relative) are ignored, and the omission is noted.

## 4. Cases (BTM)
Primary cases are in bold. Central heat rates are fixed from the lookup and recorded in §11 **before** they are run against the grid.

| Case | HR HHV central (range) | Slip kg CH4/MMBtu | Notes |
|---|---|---|---|
| **Recip 4SLB (Cat G35xx, Jenbacher)** | 8.4 (8.0–8.85; EIA IC 2025 tested = ceiling) | W-7 0.522 (≈2.8%) | W-7 and AP-42 share lineage, so they are not independent. Measured range ~1.3–3.5% |
| **Aero / simple-cycle GT (LM6000, LM2500XPRESS, Titan)** | 9.8 (9.3–11.0; EIA GT 10.975) | 0.004 | xAI-type |
| **BTM combined cycle** | 6.6 (6.4–7.0) | 0.004 | rare in the BTM fleet; shown for completeness |
| **SOFC (Bloom)** | 6.8 (6.3–7.5; lifetime-average degradation) | ~0 (vendor data if found) | 14% of identified BTM MW |
| Small rich-burn gensets (Generac-class, NSCR) | ~11.5 (11–12.5) | W-7 0.045 | shows that low slip ≠ low emissions |
| Islanded / N+1 operation (recip and SC) | +3–5% HR at 85–90% unit load | slip × 1.0–1.3 | labelled range. The only measured load curve is marine (ICCT FUMES). Islanded plants only |

Optional (O3): a fleet-weighted BTM bar using Cleanview's identified-equipment shares. Caveat: only ~30% of MW has identified equipment.

## 5. Leak cases (matched on both sides unless labelled)

| Label | L | Source |
|---|---|---|
| Low-leak supply | 0.5% | Appalachia AMI 2026, 0.52% (via EDF; the report itself not opened); NETL inventory equivalent 0.59% |
| **National measured (primary)** | **2.3%** | Alvarez et al. 2018 (gross production). Sherwin et al. 2024 corrected, 2.43%, is a six-region, oil-weighted average and is shown as a mark |
| Permian | 3.1% (2.1–3.7) | Bridger LiDAR 2024 inventory 3.13% (ES&T 2026); TROPOMI 3.2% (2023); Zhang 2020 3.7% |
| Irzak Permian | 4.0% | episode; now the high end |
| Tail | 9.4% | Chen 2022, New Mexico Permian 2018–20 only |

Labelled asymmetric scenario: BTM buys certified low-leak gas (0.5%) while the grid stays at 2.3%. Oil/gas allocation is a sensitivity: energy allocation cuts
the Permian's ~3.2% to ~1.4% (domain reviewer's arithmetic; to be recomputed from EIA Permian oil and gas output).

## 6. Grid references (per region: ERCOT = eGRID BA ERCO, PJM = BA PJM, US)
Data are eGRID2023 rev2 (latest; released 6/12/2025). Gas and coal fuel per grid MWh come from eGRID BA fields as gas share × (gas CO2 output rate ÷ gas CO2 input
rate), and likewise for coal:

| Region | Gas MMBtu per grid MWh | Coal MMBtu per grid MWh |
|---|---|---|
| ERCO | 3.63 | 1.43 |
| PJM | 3.34 | 1.50 |
| US | 3.27 | 1.74 |

- **(A) Average (attributional):** (eGRID CO2e + gas upstream [f, and CH4 at matched L] + coal-mine CH4) ÷ (1 − 3%).
- **(B) New grid NGCC built for the load (consequential, "even if it's all gas"):** H-class at 6.2 HHV (NETL H 6.196), same gas and L, ÷ (1 − 3%).
- **Primary ranking test:** BTM is worse than the grid if and only if it exceeds **both** (A) and (B). Both lines are shown.
- Context lines, not part of the test:
  - Cambium 2024 LRMER, mid-case and scenario range, levelized 2027–46, combined stage, re-based to our GWP. These are end-use rates, so no T&D is added.
    Labelled "pre-OBBBA (Aug 2024 policies), likely low".
  - eGRID non-baseload as an early-years ceiling, labelled "not a marginal rate".
- The grid is held constant at 2023 for 2027–46, which is conservative toward BTM. A declining grid (Cambium path) is a sensitivity in FaIR.
- The PJM sub-regions RFCE and RFCW are a sensitivity; they give opposite NGCC answers.

## 7. Pre-registered tests and outputs
**Primary cells:** GWP100 (AR6 fossil, 29.8) × matched L = 2.3% × region {ERCOT, PJM, US} × reference {A, B} × the four primary BTM cases.

**Tie band:** |BTM − ref| / ref < 5% counts as "tied". The band is checked with a within-cell correlated Monte Carlo: L is drawn once for both sides, the GWP draw is shared, and HR, slip, c_CH4 and f
are drawn from stated distributions. If the MC 90% interval of the difference is wider than 5%, the band is widened to match.

**Decision table per cell:**
- {CO2-only state, full state} × {above, tied, below}.
- The CO2-only state strips CH4 from **both** sides at once: BTM combustion + supply CO2 vs grid combustion CO2e + supply CO2.
- References are fixed and identical in both states.
- The decomposition is additive, Δ = ΔCO2 + ΔCH4, with the absolute gap as the primary measure.

**Break-even outputs (primary for the knife-edge cases):**
- L*, the matched leak rate at which BTM equals ref (A), and likewise for ref (B);
- the break-even facility leak for CC and SOFC;
- the break-even slip multiplier for recips (trivially "none", since recips are already above on CO2).

**Prediction recorded before running:**
- Recip, simple cycle and rich-burn are above in every primary cell, already in the CO2-only state, so methane widens the gap.
- Against (B), every BTM case is above or tied. BTM CC at 6.6 vs grid H-class at 6.2/0.97 plus supply comes out about tied to slightly above.
- Against (A) in ERCOT and PJM, CC and SOFC are tied or slightly below on CO2 and move toward above once CH4 is added. Whether they cross the 5% band is the
  open result.
- Likely honest headline: "methane widens a gap that combustion CO2 already sets for recips and turbines; for the efficient options, methane is
  what decides it."

## 8. FaIR warming (a complement to GWP100/GWP20, not a replacement)
- **Model and calibration:** FaIR 2.2.2 with calibration v1.5.1 (updated-2023; Zenodo 17424050; 841 constrained members), `ch4_method="Thornhill2021"` as in fair-calibrate.
- **Determinism:** stochastic forcing off. An A − A test must return 0. CH4 is emissions-driven.
- **Oxidation:** FaIR 2.2.2 does not oxidize CH4 to CO2, so add 2.744 kg CO2 per kg fossil CH4 to the CO2 emissions, lagged with a ~12-year e-folding (the perturbation lifetime).
- **Perturbation:** a fleet-scale step of 300 TWh/yr for 2027–2046, run for each primary BTM case and for grid references (A) and (B). Linearity is checked at half scale.
  Results are reported per TWh/yr and per GW at CF 0.7.
- **Backgrounds:** SSP1-2.6, SSP2-4.5 and SSP3-7.0.
- **Outputs:**
  - per-member ΔT difference (BTM − grid) and ratio, summarized as quantiles across members;
  - the full time series, the peak and its year;
  - ΔT in 2035, 2050 and 2100, stating that 2100 is CO2-dominated by construction.
- **Optional cross-check:** AR6 AGTP impulse-response convolution.

## 9. Sensitivities
Each is run one at a time from the primary cell. A tornado plot covers CC and SOFC against ERCOT (A).
- Heat rate ranges from §4.
- Slip: W-7 vs 2%, and the part-load bracket.
- c_CH4 range.
- f = 0.08–0.11.
- Transmission losses of 2% or 5%.
- Asymmetric grid-gas L.
- Permian oil/gas allocation.
- AR6 GWP20, and AR5 28/84.
- PJM sub-regions RFCE and RFCW.
- A declining grid (FaIR).
- Facility leaks (break-even only).

## 10. Deliverables and caveats
**Deliverables:**
- `scripts/` (emissions, grid, cases, MC, FaIR, figure).
- `results/cases.csv`, `results/decision_table.csv` and `results/breakeven.csv`.
- `METHODS.md`.
- One 16:9 figure: horizontal stacked bars (combustion CO2 / supply CO2 / slip / upstream CH4) for each BTM case at the primary L, with grid lines (A) and (B) for ERCOT and PJM.
  An inset or second panel shows L* or the GWP20 extension.
- A short Climate Brink draft and a private repo, `hausfath/datacenter-methane`.

**Caveats to state:**
- Bridge power that later connects to the grid.
- Backup vs prime power.
- The BTM redundancy penalty applies to islanded plants only.
- The Permian is oil-driven, so the marginal molecule may be Haynesville gas.
- Cambium vintage.
- eGRID 2023 vs the 2027+ grid.
- Out of scope: embodied emissions, water and local air pollution.

## 11. Changes after freeze
**2026-10-24, before any BTM-vs-grid comparison was computed.** Central parameters were fixed from `sources/lookup2/FINDINGS2.md`. HHV = LHV × 1.108. Vendor efficiencies were assumed to be LHV where the source does not say.
| Case | Central HR (HHV) | Range | Basis |
|---|---|---|---|
| Recip 4SLB | 8.40 | 7.70–8.85 | Cat G3520H 7,583 Btu/ekWh (LHV) → 8.40. Jenbacher J920 48.7% → 7.76. Wärtsilä 34SG 48.9% → 7.73. EIA IC 2025 tested 8.853 = ceiling. |
| Simple cycle / aero | 9.80 | 9.2–11.0 | LM6000PF+ 8,328 LHV → 9.23. LM2500XPRESS 8,669 → 9.61. Titan 250 8,775 → 9.72 [U]. Titan 130 9,695 → 10.74. EIA GT 10.975. Hot-ambient derate and fuel compression push real values up. |
| BTM combined cycle | 6.60 | 6.4–7.0 | unchanged |
| SOFC (Bloom) | 6.40 | 5.81–7.13 | Feb 2026 datasheet: "Cumulative electrical efficiency 65-53% (LHV net AC)", 5,811–7,127 Btu/kWh HHV. Central = midpoint (59% LHV), the BTM-favourable end. The brochure's "average lifetime electrical efficiency 54%" (7.0 HHV) is a sensitivity. No CH4 data exists, so slip is 0. |
| Rich-burn small genset | 11.6 | 11.0–12.5 | Generac SG500 prime 5,238 scf/h at 450 kW × 1,000 Btu/scf (assumed) |
| Grid NGCC (ref B) | 6.20 | | NETL H-class 6.196 |

- Coal-mine CH4: 0.199 kg CH4 per MMBtu of coal (EPA GHGI 1990–2023, 1,623 kt in 2023, ÷ EIA 2023 coal consumption 8.17 quads). Abandoned mines are excluded; including them gives 0.226, which moves the grid by about 1 kg/MWh.
- Transmission loss stays at 3%, the BTM-favourable choice. The lookup found no primary transmission-only figure; its judgment is ~2% (1–3%). Sensitivities: 2% and 5% T&D.

**2026-10-24, V3 result: FaIR does not cleanly reproduce the AR6 CH4 metrics on an SSP2-4.5 2030 background.**
- GWP100-like: 37.2 (5–95%: 29–47), against AR6 non-fossil 27.0 ± 11 [from memory, verify].
- GTP100-like: 8.0 (3.2–15.2), against 4.7 ± 2.8.
- Diagnosis:
  - Ozone forcing per pulse is 0.61× the direct CH4 forcing.
  - The perturbation e-folding is 13.2 yr.
  - CO2 AGWP100 is 7.95e-14, against AR6 8.95e-14.
- Consequence: FaIR weights CH4 more heavily than GWP100 does, which works against BTM. The FaIR results stay a complement and are labelled with this calibration
  offset. GWP100 remains primary. The optional AR6 AGTP convolution is promoted to "do if time permits" as the AR6-consistent cross-check.
