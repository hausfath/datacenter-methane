# Off-grid gas for data centers: per-MWh CO2e with methane (pre-analysis plan, v1.1 DRAFT)

Source idea: brink-ideas PR #36 (approved 2026-10-24). Status: draft for review, nothing run except the Frost feasibility arithmetic in §2.

## 1. Question and claim under test
Zeke's claim (Bluesky/X, 24 Oct 2026): data centers that get built should connect to the grid, not run on behind-the-meter (BTM) gas.
The question: per MWh delivered to a data center, how do the emissions of BTM gas compare with the grid, including methane slip from engines and
upstream leakage? Does methane change the **ranking** (which option is worse), or only the **size of the gap**?

Because the claim being tested is Zeke's own, methodological choices that can go either way are resolved **in favour of BTM gas** (that is, against the
claim). The alternative is run as a sensitivity.

## 2. Validation steps (both run before anything else)
V1. **Bottom-up model vs NETL.** Reproduce NETL Rev1 (DOE/NETL-2025/4933) NGCC-F at 394.7 kg CO2e/MWh generated, 0.55% leakage (kg CH4 per kg NG
    delivered), using our own emissions function with NETL's heat rate and leak definition. Pass if within ±3%. Also check the NETL fleet peaker
    (659.7, 34.5% HHV).
V2. **Frost fleet numbers (consistency, not a unique reproduction).** Frost (Latitude Catalyst, 22 Oct 2026, transcript saved in
    `sources/latitude_catalyst_irzak.txt`): 50 GW, 18 months, "7.5% of methane ends up in the atmosphere", 380 Mt CO2e (100-yr), 724 Mt (20-yr),
    "between 50 and 60% is CO2 and between 40 and 50% is methane". The episode does not give heat rate, capacity factor or the base of the 7.5%.
    The 724/380 ratio pins the CH4 per MMBtu; the 380 total pins CF × heat rate. Feasibility arithmetic with AR5 GWPs (28/84, which Irzak quotes)
    gives 1.57 kg CH4/MMBtu (≈8.8% of delivered CH4), a 45% CH4 share at GWP100 (inside her 40–50%), and CF × HR = 5.96 MMBtu/MWh
    (CF 0.70 at 8.5 MMBtu/MWh). With AR6 GWPs, the implied CH4 share is 51%, just outside her range, so she probably used AR5.
    Report: Frost's numbers are internally consistent with plausible inputs, and the 7.5% maps to about 8–9% of delivered methane. Flag the 18-month
    framing (it treats 50 GW as running for the full 18 months, which is faster than the build-out).
    Decompose the 7.5%: Irzak says it bundles "facility leaks ... the upstream, midstream, and engine slip". The implied ~8.8% of delivered CH4
    minus W-7 slip (~2.9%) leaves ~5.9% for upstream + midstream + facility, against her stated 4% Permian wellhead + gathering. Report this split.
    That shows what she assumed for the parts she did not state.

## 3. Emissions function (per MWh net delivered to the data center bus)
E = HR × [ EF_CO2 + GWP × ( m_slip + m_up + m_fac ) + GWP_N2O × m_N2O ] (+ grid T&D for grid cases)
- HR: fuel input, MMBtu **HHV** per MWh net, including site parasitics. W-7, AP-42, Table C-1 and EIA heat rates are HHV. Vendor efficiencies
  and kJ/kWh figures (GE Vernova, Jenbacher, Wärtsilä) are LHV and are converted with HHV/LHV = 1.108 (explicit parameter). Every heat rate in the
  case table carries an HHV/LHV label.
- EF_CO2 = 53.06 kg/MMBtu (40 CFR 98 Table C-1).
- m_slip = engine slip, kg CH4/MMBtu: 40 CFR 98 Table W-7 (May 2024 rule) 4SLB 0.522, 2SLB 0.658, 4SRB 0.045, gas turbine 0.004; AP-42 Table 3.2-2
  4SLB 1.25 lb/MMBtu (0.567 kg) as a cross-check. AP-42 says these are factors "for engines at all loads", **not** full load as the episode says.
- m_up = upstream + midstream CH4 per MMBtu delivered = c_CH4 × L / (1 − L), where L is the loss as a share of CH4 produced and c_CH4 is the CH4 content
  of delivered gas (about 17.8 kg/MMBtu at 95 mol% CH4 and 1.026 MMBtu/Mscf; sensitivity 0.884–0.970 mass fraction per NETL).
- m_fac = on-site and transmission leaks (sensitivity only; no dataset).
- Supply-chain CO2 (processing, compression fuel, flaring) = f × combustion CO2, f = 0.10 (0.08–0.11, EIA/NETL; same value as the clean_energy_lca
  project). This term was missing from v1. Without it, NGCC comes out ~34 kg/MWh low against NETL. It applies equally to BTM gas and to grid gas.

**V1 result (run 2026-10-24, `scripts/v1_netl_check.py`):** 393.6 vs NETL 394.7 (−0.3%). The upstream CH4 term is 21.1 vs NETL's 21.0. Caveat: f was
taken from the same NETL/EIA family, so the total is partly calibrated. The CH4 term is the independent check.

## 4. Cases
Prime movers (BTM):
| Case | HR (MMBtu/MWh, HHV) | Slip |
|---|---|---|
| Recip 4SLB, full load | from lit scan (modern gensets ~8.0–8.8) | W-7 0.522 (≈2.9%) |
| Recip 4SLB, part load / N+1 spinning | HR penalty from lit scan | **labeled range, no central value**: EPA factors are already "all loads", so the part-load premium over them has no EPA anchor, and 12% is anecdotal (Irzak). Use measured load dependence if the lit scan finds it. |
| Aeroderivative / simple cycle GT | ~9.5–10.5 (EIA, vendor) | 0.004 |
| Combined cycle (BTM, e.g. large campus) | ~6.4–7.0 | 0.004 |
| Fuel cell (SOFC), optional | vendor ~ 6.5–7.5 | ~0 |

Upstream loss L (share of CH4 produced): 0.2% (MiQ A, best operators), 0.55% (NETL inventory basis, converted), 2.43% (Sherwin et al. 2024, corrected
May 2026), 4% (Permian per Irzak; check against Zhang 2020, Varon 2023 and newer satellite/aerial estimates), and the highest published Permian value
as a tail.

Metrics: AR6 GWP100 (fossil CH4 29.8) primary; AR6 GWP20 (82.5); AR5 28/84 only for the Frost comparison. N2O at 273 (minor).

## 5. Grid comparison
- Average: latest eGRID (BA/subregion output rates: US, ERCOT, PJM). Add (a) upstream CH4 for each grid's gas-fired fuel use at the national measured
  L (2.43%, Sherwin corrected), because grid gas is national-average supply, with a Permian-L grid as a sensitivity for ERCOT only; (b) T&D losses
  (~5%, EIA). Both raise the grid number, which is conservative toward BTM. (One grid line per region, not one per leak case. Reviewers: is this
  the right conservative choice?)
- Marginal: NREL/NLR Cambium LRMER (latest workbook) for the ERCOT and PJM GEA regions, 2027 start and 20-yr evaluation, with combustion + precombustion.
  Check Cambium's own leak rate and GWP and re-base it to ours. SRMER (Cambium or eGRID non-baseload) as a second marginal view.
- Primary reference line: **whichever of average and LRMER is higher** for each region (conservative toward BTM). Both shown.

## 6. Warming per TWh (horizon-free check)
FaIR 2.2.2 (python3.13), calibration v1.4.x constrained ensemble (check latest). 1 TWh/yr gives ~1e-6 K, inside numerical noise, so the
perturbation runs at fleet scale: 50 GW × CF 0.7 ≈ 300 TWh/yr held constant for 20 years (2027–2046) for each option. Baseline and perturbed runs use
identical configs and the difference is taken member by member. The background is SSP2-4.5, with CMIP7 Medium as a sensitivity if easy. Linearity is
checked by repeating at half scale, and results are reported per TWh/yr. Report ΔT in 2035, 2050 and 2100 (median and 5–95%) and the BTM/grid ratio
over time. This replaces any argument about GWP20 vs GWP100.

## 7. Pre-registered interpretation (from the PR, made precise)
The size of the methane share is already fixed by arithmetic. At W-7 slip and L = 2.43%, CH4 is about 0.97 kg/MMBtu × 29.8 ≈ 29 kg CO2e/MMBtu against
53 for CO2, which is ~35% of a recip's GWP100 total and ~20% for NGCC. The PR's "methane adds little" kill test therefore cannot fire on size and is
dropped. The open question is **ranking**:
- **Ranking changes** if a BTM case sits below the grid reference on CO2 alone but above it once CH4 is included, at GWP100 with L ≤ 2.43%.
- **Methane widens, doesn't create, the gap** if every BTM case that ends up above the grid reference is already above it on combustion CO2 alone.
  Expectation to check, not assume: a recip at ~8.4 MMBtu/MWh emits ~445 kg CO2/MWh from combustion alone, which may already exceed the ERCOT and PJM
  averages. If so, the write-up must not present methane as the deciding factor.
- **Interesting/narrowing:** recip on Permian-like gas exceeds the ERCOT reference at GWP100 while low-leak NGCC does not → the argument narrows to
  "no recips on high-leak gas".
Record whichever outcome occurs.

## 8. Sensitivities
Grid: average vs LRMER vs SRMER; with and without T&D and upstream on grid gas. BTM: heat rate ±; redundancy/part load; slip W-7 vs AP-42 vs
measured; c_CH4 range; facility leaks 0–0.5%; Permian wet gas (lower CH4 fraction); AR5 vs AR6 GWPs. Out of scope (noted as caveats): bridge power
that later connects to the grid; grid build-out induced by the load (partly in LRMER); data center water/cooling; embodied emissions.

## 9. Deliverables
`scripts/` (emissions function, case table, FaIR runs, figure), `results/cases.csv`, `METHODS.md`, one 16:9 figure (stacked horizontal bars: combustion
CO2 / slip / upstream CH4, by case, with grid reference lines; GWP20 as a second panel or outline), a short draft of the text, a private repo
`hausfath/datacenter-methane` to be made public later.

## Notes added while the reviews ran (2026-10-24)
- Lit scan (`sources/lit_scan/FINDINGS.md`): latest eGRID is still eGRID2023 rev2. The US total output rate is 770.9 lb CO2e/MWh (≈350 kg) and ERCT is 736.6
  (≈334 kg); non-baseload rates are 1,379 and 1,248 lb. EIA Table 8.2 gives 2025 tested heat rates of CC 7,535, GT 10,975 and IC 8,853 Btu/kWh.
  An IC engine therefore emits ≈470 kg CO2/MWh from combustion alone, which already exceeds the eGRID US and ERCT averages before any methane. For
  context, Cleanview's tracker lists about 90 GW of planned BTM capacity, with 2 GW operating. [Equipment-by-manufacturer detail removed at Cleanview's request.]
- Cambium 2024 workbook (downloaded to `data/cambium/`) has levelized LRMER, combustion and precombustion, by GEA region and for 8 scenarios. **Caveat:**
  its policy assumptions date from Aug 2024, with the IRA intact. The 2025 law changes (OBBBA credit phase-outs) are not in it, so its post-2027
  marginal rates are probably too low, which flatters the grid. NREL also says not to use it for near-term (2020s) conditions. Options: the 2025
  annual value held flat; the "High RE cost + Low NG price" scenario as a post-OBBBA proxy; eGRID non-baseload as an SRMER-like upper reference.
