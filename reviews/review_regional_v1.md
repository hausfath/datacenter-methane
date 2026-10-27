# Review of PLAN_regional.md (draft R1): combined domain + methods

Reviewer: combined domain (gas-supply methane, power-sector accounting) and methods reviewer, 2026-10-24.
Scope: `PLAN_regional.md`, `data/basin_leak_rates.json`, `sources/basins/BASINS.md`, `PLAN.md`, `METHODS.md`, `scripts/cases.py`, `scripts/emissions.py`, `scripts/grid.py`, `scripts/regional.py` (code read only), `data/grid_inputs.json`, `sources/lit_scan/FINDINGS.md` §5 and the saved Cleanview page.

**What I did not do.** I did not run `regional.py` and computed no BTM-vs-grid comparison for any region. All numbers below are either read from input files or are input-side arithmetic (one side of the comparison only: grid-side terms, or the change in the BTM upstream term with L). None is a regional verdict.

**Tags.** [OPENED] = I read it in a local file or ran it on local input data in this review. [BASINS.md] = taken from the subagent compile, with its own tag carried over. [MEMORY] = from my own knowledge, not verified here; treat as a lead to check.

---

## Bottom line

The addendum asks the right question, but four things need fixing before it runs. Each would change which grid or which basin a region is tested against:

1. Two site-to-grid assignments are wrong or contested. Crusoe Goodnight is in SPP, not ERCOT. Colossus 2's turbines sit at a site eGRID puts in the TVA BA, yet the plan uses MISO.
2. The grid-factor rule does not follow its own stated principle. In NM it takes the lower candidate and in WY/UT the higher one. A single consumption-based rule is available from EIA-930.
3. Two basin pairings are inconsistent with the plan's own rule and with physical supply. Wyoming uses DJ alone; Utah uses Uinta, which could not physically supply a multi-GW campus.
4. §7 contains a logic error about which reference binds, and it understates the leak-rate effect by about an order of magnitude.

The tie-band reuse is not acceptable for coal-heavy or high-L regions, and re-running the MC is cheap.

---

## MUST-FIX (before any regional run)

### M1. Crusoe Goodnight is not in ERCOT; the Panhandle is missing as a region
- Cleanview lists the Crusoe Goodnight campus in Armstrong County, TX [quoted Cleanview detail removed at Cleanview's request].
- The Cambium 2024 County Mapping sheet maps Armstrong County, TX to ReEDS BA p48, GEA **SPP_South** [OPENED, `data/cambium/Cambium24_Workbook.xlsx`].
- eGRID2023 places the neighbouring Panhandle plants (Harrington and Nichols in Potter County) in **BA SWPP / subregion SPSO** [OPENED, `egrid2023_data_rev2.xlsx` PLNT23].
- Cleanview also lists Fermi America's Project Matador near Amarillo, TX [quoted Cleanview detail removed at Cleanview's request]. It is the largest single BTM project in the tracker, and it is also in SPP.
- Gas supply in the Panhandle is plausibly Anadarko or Permian, not the Permian alone [MEMORY]. BASINS.md gives Anadarko 1.7% (1.4–2.1%) [BASINS.md, VERIFIED-FULLTEXT].
- **Fix.** Remove Goodnight from the West Texas row. Either add a "Texas Panhandle (SPP / SPSO)" region with an Anadarko–Permian pairing, or state explicitly that the Panhandle is excluded and why. The plan claims to cover "every region where BTM data centers are actually being built", and as written it omits the largest project.

### M2. Southaven / Colossus 2: the plan's MISO assignment is contested by the data
- Cleanview places xAI's Colossus 1 and 2 in Memphis, TN and Southaven, MS, with Colossus 2's behind-the-meter power at the old Southaven Power Plant site [quoted Cleanview detail removed at Cleanview's request].
- eGRID2023: "Southaven Combined Cycle Plant", DeSoto County MS, is **BA TVA / SR SRTV** [OPENED, PLNT23].
- Cambium maps DeSoto County to MISO_South [OPENED]. The county is therefore split between service territories in at least one dataset.
- The relevant counterfactual grid is the one that would serve the **load**, not the turbines. Colossus 2's data hall is in Memphis (Tulane Road area, MLGW/TVA) [MEMORY, verify]. If so, both xAI sites are TVA cases and the MISO row is a mis-assignment.
- The plan picks the MISO BA rate (448 kg/MWh), which favours BTM. eGRID's SRMV subregion (MISO South) is 337, and TVA BA is 292 [OPENED, `grid_inputs.json`]. The decomposition below shows that MISO BA generation is mostly outside MISO South:

  | MISO BA generation by eGRID subregion of plant [OPENED] | TWh | kg CO2e/MWh |
  |---|---|---|
  | SRMV (MISO South) | 176 | 337 |
  | MROW | 157 | 367 |
  | RFCW | 102 | 613 |
  | RFCM | 84 | 447 |
  | SRMW | 79 | 560 |
  | (total BA) | 652 | 448 |

- **Fix.** Pin down, from permits or utility filings, which utility would interconnect Colossus 2's load. Until then run TVA as primary for both xAI sites, and if MISO is kept, use SRMV (MISO South) rather than the MISO-wide BA. MISO BA mostly reflects Midwest coal that does not serve DeSoto County.

### M3. The grid-factor rule: replace the per-region choice with one rule, preferably consumption-based
The draft's choices, with the rate each one picks and the one it passes over:

| Region | Chosen primary | Rejected candidate | Direction of choice |
|---|---|---|---|
| NM / El Paso | AZNM 320 | EPE BA 459 | **lower** (anti-BTM) |
| Wyoming | WACM BA 854 | RMPA 473 | higher (pro-BTM) |
| Utah | PACE BA 644 | NWPP 288 | higher (pro-BTM) |
| Memphis | TVA BA 292 | SRTV 410 | lower (anti-BTM) |
| Southaven | MISO BA 448 | SRMV 336 | higher (pro-BTM) |

So the rule is not "conservative toward BTM", and it is not "subregion for small BAs" either. It is region-by-region judgment, which is the most gameable option. Several of these choices are individually defensible, as the next list shows, but the set has no single principle.

**Why neither "BA everywhere" nor "subregion everywhere" works.** Plant-level decomposition [OPENED, PLNT23, plant CO2e ÷ plant net generation; it reproduces the eGRID BA rates]:
- **WACM** = 23.6 TWh assigned to RMPA (762 kg/MWh) + 13.2 TWh assigned to **MROW** (1,043 kg/MWh). The MROW portion is Laramie River (9.46 TWh, Platte County WY) and Dry Fork (2.85 TWh) [OPENED: BA WACM, SR MROW]. My reading of that assignment is that their output serves MRO loads (Basin Electric and its members), not Cheyenne [inference; ownership from MEMORY]. The production-based WACM rate (854) therefore includes plants that eGRID assigns to other consumers.
- RMPA, the alternative, is 57% PSCO (Colorado Front Range: 38.3 of 67.7 TWh), so it is not a Cheyenne rate either. A third, eGRID-internal option exists: WACM-RMPA-only at 762.
- **PACE** is all within NWPP. NWPP is dominated by BPAT hydro (94.9 of 269 TWh), so NWPP 288 is a poor proxy for what central Utah consumes. Intermountain (Millard County, the Joule county) is **BA LDWP / SR CAMX**: it exports to Los Angeles [OPENED].
- **SRTV (410)** includes LG&E-KU (LGEE, 31.0 TWh) and PJM-assigned plants (9.6 TWh at 773). TVA BA (292) is the cleaner local rate, so SRTV is not a valid "alternative" for Memphis.
- **EPE** generated only 6.2 TWh in 2023 [OPENED]. EPE's retail load is larger, and it owns a share of Palo Verde nuclear, which sits outside its BA [MEMORY]. Its production rate (459, 89% gas at 9.76 MMBtu/MWh) is therefore likely well above its consumption rate. AZNM is dominated by SRP, NEVP and AZPS.

**Consumption-based rates are obtainable from EIA directly.** The EIA-930 "About" page says EIA calculates "both the CO2 emissions intensity of generation (or, the production emissions intensity) and the CO2 emissions intensity of load (or, the consumption emissions intensity) for each BA ... using a multiregional input–output model (MRIO)" [OPENED, `sources/lit_scan/eia930_about.html`].

Limitations of that source [OPENED, same page]:
- CO2 only.
- CHP excluded.
- Only BA-metered generation is covered.
- National average emission factors are used for non-fossil fuels.
- Canada and Mexico imports are assigned the US average.

Open Grid Emissions (Singularity) and the Stanford gridemissions dataset (de Chalendar et al.) also publish consumption-based BA rates [MEMORY; check year coverage for 2023].

**Recommendation (least gameable).**
- **Primary for all seven regions:** the EIA-930 2023 consumption (load) CO2 intensity of the BA serving the load, scaled to CO2e with eGRID's BA CO2e/CO2 ratio.
- **Fuel terms.** For the upstream-gas and coal-mine terms, scale the eGRID BA gas and coal MMBtu/MWh by the consumption/production CO2 ratio. That is a first-order assumption that imports carry the BA's own fuel mix; say so. Better, run the same MRIO on fuel MMBtu, which the de Chalendar method supports [MEMORY].
- **Bracket:** report the eGRID production BA rate and the eGRID subregion. Call a regional verdict robust only if it holds at both ends of the bracket and at the consumption value. Otherwise call it "grid-factor-dependent".
- **Fallback.** If the EIA-930 consumption data cannot be retrieved for 2023 before the run, use **one** mechanical rule for all seven regions: eGRID subregion (EPA's location-based convention [MEMORY]) with BA as the sensitivity, or max(BA, subregion) if the "conservative toward BTM" rule is to govern. Freeze the choice before the run. Do not mix the two.
- **Region-specific additions:**
  - Wyoming: add WACM-RMPA-only (762) as a sensitivity.
  - El Paso: note the Palo Verde ownership point.
  - Remove PNM as an El Paso alternative. Both projects sit in EPE's service territory: Jupiter is in Doña Ana County, and Meta's is in El Paso, TX. Every Doña Ana generator except Afton is in BA EPE [OPENED]. PNM BA (179) is Albuquerque's grid.

### M4. Utah basin pairing violates the plan's own rule and fails a physical-scale check
- The plan says Kern River (Wyoming) gas is possible "which makes Uinta the conservative choice toward the grid". The plan's rule is to be conservative toward **BTM**, so by its own logic it should not pick Uinta as central.
- **Scale check** (inputs only):
  - MacKay 2026 Table 1 gives Uinta 2023 gas at 46 Mboe, about 7.8 bcm or 276 Bcf per year [BASINS.md, VERIFIED-FULLTEXT; conversion 169.9 m3/boe is MacKay's].
  - Joule's announced 4 GW of Cat G3520K [OPENED, Cleanview] at HR 8.4 and CF 0.8 burns about 227 Bcf per year, **about 82% of all Uinta gas production**.
  - At the 12 GW full build-out Cleanview reports, the burn is about 250% of Uinta production.
  - The Uinta basin therefore cannot be the physical supplier at scale, let alone the marginal one. Supply would be Rockies pipeline gas (Kern River from Opal/Greater Green River, Questar from Uinta/Piceance) [MEMORY: pipeline routing through or near Millard County not verified].
- **Fix.** Make the Utah central a Rockies supply mix, or use Greater Green River (5.2%) as the BTM-favourable central, with Uinta 6.5–8% as high. Note that the Rockies alternatives are also high-L: GGR 5.2% (low confidence, 44% coverage) and Piceance 7.9% [BASINS.md, MacKay]. The practical change in L is therefore only about 1–1.5 points. The rule inconsistency is the bigger problem.

### M5. Wyoming basin pairing: DJ alone is the most BTM-favourable option on the table and should be labelled as such
- Cleanview lists Crusoe/Tallgrass Project Jade in Laramie County, WY, combining Bloom fuel cells and gas turbines [quoted Cleanview detail removed at Cleanview's request].
- Tallgrass operates or owns stakes in Rockies Express and other pipelines out of the Cheyenne Hub. That hub aggregates Greater Green River, Piceance, Powder River, Wind River and DJ gas [MEMORY].
- The likely physical supply is therefore a Rockies mix, not DJ alone. The candidate basins:
  - DJ 1.2% [BASINS.md].
  - GGR 5.2%, low confidence [BASINS.md].
  - Piceance 7.9%, from MacKay; tag not stated in BASINS.md.
  - Powder River: no measurement (gap).
- **Fix.** Either use a production- or flow-weighted Rockies mix as central, with DJ as low, or keep DJ central but label it in §6 and in the output as "the most BTM-favourable defensible basin". Show the GGR case with equal prominence in the basin-range bars.
- **Also check** whether Jade's turbines are paired with CO2 capture through Tallgrass's Wyoming sequestration hub [MEMORY, unverified]. If they are, the simple-cycle case does not describe this project.

### M6. §7 has a logic error and a magnitude error

**Logic.** "...every BTM option including recips may come out below grid A. They remain above or tied with B, so the two-condition verdict is still 'not worse', and in those regions the binding comparison becomes B."
- Under "worse iff above A AND above B", the test is equivalent to "above max(A, B)".
- Where A > B (coal-heavy grids), the binding reference is **A**, not B. If BTM is below A, the verdict is "not worse" whatever its position relative to B.
- In the main analysis (A ≈ 408–432 < B ≈ 455 at L = 2.3%) the binding reference was B.
- The prediction should say: "In WY/UT, the AND test reduces to a comparison with A, so it will return 'not worse' for any option below the 2023 coal-heavy average, including options well above a new NGCC."
- This is a framing problem (see M7), not just a wording slip.

**Magnitude.** "Basin leak rates change totals by tens of kg/MWh" understates the effect. From `emissions.py` alone (BTM side only, c_CH4 = 18.7, BTM loss 1%):

| BTM case | ΔE from L = 2.3% → 6.5% (Uinta central), GWP100 | same, GWP20 | per +1 pt L near 2% |
|---|---|---|---|
| Recip (HR 8.4) | +217 kg/MWh | +602 | ~50 |
| Simple cycle (9.8) | +254 | +702 | ~58 |
| SOFC (6.4) | +166 | +459 | ~38 |
| CC (6.6) | +171 | +473 | ~39 |

Grid-side sensitivity per +1 pt L (gas MMBtu/MWh × the same factor, ÷ 0.97), from `grid_inputs.json`:

| Grid | kg/MWh per +1 pt L | Gas MMBtu per grid MWh |
|---|---|---|
| WACM | 4.8 | 0.79 |
| PACE | 11.4 | |
| TVA | 14.9 | |
| MISO | 17.6 | |
| PJM | 20.2 | |
| ERCO | 22.0 | |
| AZNM | 22.6 | |
| **EPE** | **52.2** | **8.64** |

- Basin L therefore moves the gap by hundreds of kg/MWh in high-L basins with coal-heavy grids, not tens.
- PLAN.md §1 says "BTM burns more gas per MWh than the grid's gas share, so the ranking can only flip one way". That premise **fails for EPE**: 8.64 MMBtu/MWh exceeds SOFC (6.4) and CC (6.6). If EPE is used, higher matched L moves the efficient options toward the grid. State this before running.

**Well-posedness.** Predictions should be stated per region × case × reference, not as a summary.
- Include Southaven (and the Panhandle, if added). The current list omits MISO.
- Record **which of A or B is larger in each region**. That needs only grid-side inputs, so it is legitimately pre-registrable.
- For each efficient case, predict whether its vs-B verdict changes with L. Under matched pairing it should be nearly L-invariant, because BTM and B burn similar gas. It can move only through the local-vs-national asymmetry.

### M7. Report a four-state classification, and pre-register the framing for regions where A > B
The two-condition test was designed for grids cleaner than new gas (A < B), where it gives BTM the benefit of the doubt. In coal-heavy grids it becomes "above A" only, so a recip 50–60% above a new NGCC could be reported as "not worse than the grid". That is literally true against the 2023 average and misleading as a claim about building on the grid.

Recommendation: keep the AND test as the pre-registered "worse" verdict, and add mutually exclusive states, each defined against the MC band:
- **Worse:** above A and above B.
- **Between:** below or tied with one reference, above the other. Report which one, for example "cleaner than the 2023 Wyoming average, dirtier than new grid gas".
- **Better:** below both.
- **Tied:** within the band of both.

Pre-register the headline sentence for "Between" cells now. A sentence like this concedes the true part and is honest: "On a 2023-average basis, gas on site beats Wyoming's coal-heavy grid. It still emits X% more than a new gas plant on the grid would, and the coal comparison weakens as [named units] retire." Also concede the counter-point: large new load in a coal-heavy BA can delay coal retirements (see S4), which would make "connect to the grid" worse than the average implies.

### M8. Coal-mine methane: the national factor is a tie-band-sized term in WACM/PACE with region-specific bias
Grid-side coal-mine CH4 at the national 0.199 kg/MMBtu, inputs only:

| Grid | GWP100 kg CO2e/MWh | GWP20 kg CO2e/MWh |
|---|---|---|
| WACM | 51.7 | 143 |
| PACE | 34.3 | 95 |
| RMPA | 22.4 | |
| SRTV | 19.0 | |
| MISO | 18.2 | |
| TVA | 10.2 | |

- WACM's coal is mostly Powder River Basin surface coal (Laramie River, Dry Fork, Wygen, Neil Simpson are all in Campbell or Platte County, WY [OPENED, PLNT23, plant locations]; the coal origin is [MEMORY]). PRB surface coal has very low in-situ gas content [MEMORY]. The national factor, which is dominated by Appalachian, Black Warrior and Illinois underground mines [MEMORY], likely overstates WACM's term several-fold. That is a **pro-BTM bias** of perhaps 40 kg/MWh at GWP100 and over 100 at GWP20, about 5% of A. Order of magnitude only; it depends on the unverified factor ratio.
- PACE burns Utah underground coal (Hunter, Huntington in Emery County [OPENED, PLNT23]; the mine type is [MEMORY]) plus Wyoming surface coal (Dave Johnston, Wyodak, Jim Bridger [MEMORY for Bridger]). The direction of the bias there is unclear.
- **Fix.** Use basin- or mine-type-specific factors. Two routes [MEMORY, verify]:
  - EPA GHGI Annex 3.4 basin-level surface and underground emission factors.
  - EIA-923 Schedule 2 fuel receipts, which give mine type and county of origin by plant. These can be joined to GHGRP Subpart FF mine-level ventilation CH4 for underground mines.
- If neither can be done before the run, carry a pre-registered range on the CMM factor (for example 0.02–0.25 kg/MMBtu for PRB-heavy grids) and put it in the MC (S1).
- **Latent issue in the main analysis (flag).** The gas side carries supply-chain CO2 (f = 0.093), but the coal side carries no mining or rail CO2. NETL coal LCAs put coal supply-chain CO2 at roughly 1–3% of combustion CO2 [MEMORY]. The effect on A, using the eGRID coal MMBtu above with ~95 kg CO2/MMBtu and 2%:
  - ERCOT/PJM: about 3 kg/MWh (<1% of A), so it does not affect the main results.
  - WACM: about 16 kg/MWh.
  - The omission biases A **down**, which is anti-BTM. It partly offsets the CMM bias in WACM. Add a coal supply-CO2 term or state the bound.

### M9. Code issues in `regional.py` (read only)
- `import cases as cs` executes all of `cases.py` at module level: the case table, decision table, break-even, the 20,000-draw MC, sensitivities and every `to_csv` [OPENED]. Running the regional script therefore regenerates and overwrites `results/*.csv` from the main analysis. The seed is fixed, so the outputs are identical today, but any later edit to `cases.py` would silently change the main results through the regional run. Move the main computations under `if __name__ == '__main__':` or into functions. The smoke-test run also rewrote the main results files; `git status` after it shows no changes to tracked `results/*.csv` [OPENED], so the rewrite was byte-identical.
- `gas_boe_share` is loaded from the JSON but never used. The energy-allocation sensitivity promised in §3 and §6 is not implemented.
- The tie band from the GWP100 MC is applied to the GWP20 rows. That is acceptable only if labelled; the GWP20 band should be wider.
- In the "local BTM, national grid gas" pairings, **B is evaluated at national L** (`grid_ngcc(Lg)`). B is a hypothetical new plant built in the region for this load, and it would burn regional pipeline gas. The asymmetry argument ("grids draw pipeline-mixed supply") applies to the existing fleet (A), not to B. Evaluating B at national L in a high-L region biases against BTM. Run B at the local L in all pairings, or show both.

---

## SHOULD-FIX

### S1. Do not reuse the main tie bands; re-run the MC per region (Q3)
- The reuse rationale ("avoids re-running 6 × 5 times") is weak. The main MC is about 700k scalar function calls and takes minutes, and it vectorizes easily.
- The reused bands are wrong in both directions.
  - **High-L basins (Permian TX, Uinta, GGR):** the main MC drew L ~ N(2.3%, 0.35%). Basin ranges are 2.4–4.2% (Permian TX) and 5.5–8% (Uinta). Under matched pairing, L does not cancel when grid gas per MWh is small (WACM 0.79 vs BTM 6.4–9.8). Bands are therefore understated, which gives too many "above" verdicts (anti-BTM).
  - **Coal-heavy A:** the band is relative to A. With A two to three times larger than in the main regions and a similar absolute BTM spread, the reused relative band is overstated. That gives too many "tied" verdicts, which matters for the "Between" and "Better" states in M7.
  - **Grid-side structure:** the main MC never varied CMM or coal-side factors, and the coal heat rate is fixed inside eGRID. In WACM/PACE, CMM uncertainty (M8) is of the same order as the band.
- **Fix.** Per region, draw L from the basin's low/central/high, for example triangular. Under matched pairing, share the draw across both sides and B. Add a CMM-factor draw (range per M8). Keep the other draws as in the main MC. Keep the grid-factor choice out of the MC: it is structural, and is handled by the M3 bracket.

### S2. Matched pairing: state the tilt per region; the existing sensitivity is the right bracket (Q2)
Compared with the "grid at national 2.3%" alternative, matched pairing:
- **raises A** in high-L basins (Permian TX, Uinta, GGR), which favours BTM. ERCOT's fleet burns a Texas-wide mix (Permian, Haynesville, Eagle Ford, Barnett [MEMORY]), not Permian alone. At 22 kg/MWh per point of L, assigning Permian TX 3.6% instead of a ~2.5% Texas mix inflates ERCOT A by about 25 kg/MWh, about 6% of A. That is enough to matter near the SOFC tie.
- **lowers A** in low-L basins (Appalachia, Haynesville), which works against BTM relative to national.

Both pairings are already in the code. State this tilt in §4, and do not call a verdict robust unless it holds under both.

### S3. Basin-value consistency (Q2 values)
- **Permian TX** mixes basin-wide and Texas-side values.
  - Low 2.4% is MacKay's **basin-wide** (TX+NM) value [BASINS.md].
  - High "Varon 2023 upper ~4.1" is Varon's **basin-wide** 3.2 ± 0.9%. Varon's TX 2023 is 3.6 ± 1.0, upper 4.6 [BASINS.md, VERIFIED-FULLTEXT].
  - MethaneSAT TX 3.1% (2024–25, marketed denominator, not peer reviewed) is not used [BASINS.md].
  - A consistent Texas-side range is about 3.1 / 3.6 / 4.6. The draft's 2.4 / 3.6 / 4.2 is skewed low, which favours BTM. That is allowed under the rule, but label it.
- **Permian NM.** The high of 4.5% is Varon's **2019** NM value, while the TX high uses 2023-era values. Varon NM 2023 is 2.1 ± 0.7 (upper 2.8) [BASINS.md]. Use 2023-consistent ranges on both sides, or run a "2019 backsliding" case for both TX and NM.
- **"Permian NM side" label.** The Delaware sub-basin straddles TX and NM [MEMORY], and gas at Waha and on the El Paso Natural Gas system is commingled. Meta El Paso is **in Texas**, and Jupiter is supplied from the same pipeline system [MEMORY]. Assigning the NM-state intensity (2.1%) rather than basin-wide (~3.1–3.2%) favours BTM. Recommend basin-wide Permian (Bridger 3.13%, Varon 3.2%, MacKay 2.4%) as central for the El Paso/NM region, with the NM state value as the low.
- **Appalachia** (0.4/0.6/0.9) and **Haynesville** (0.4/0.7/1.0) match BASINS.md. Memphis supply is a pipeline mix of Haynesville, Gulf Coast and reversed-flow Appalachian gas [MEMORY]. Both basins are low-L, so the verdict should be insensitive to the choice.
- **Definition mismatch with METHODS.** METHODS defines L as "whole chain through transmission". The basin values exclude transmission and storage outside the basin and local distribution (BASINS.md gap 12), while the national 2.3% (Alvarez) includes them.
  - In the local-vs-national sensitivity, the grid therefore carries transmission and storage that BTM does not. Alvarez's segment split puts that share at about 0.3 percentage points [MEMORY: T&S ~1.8 of 13 Tg]. This biases toward BTM.
  - For off-basin sites (Vineland, Sterling, Memphis, Cheyenne, Utah), add a transmission increment to the basin L on both sides. In-basin sites (Abilene, Frontier, Monarch) can go without.
- **Denominators.** Fine as stated ("a few percent relative"). MacKay uses gross gas while MethaneSAT and AMI use marketed gas, which pushes the MethaneSAT and AMI lows slightly higher on a gross basis. Negligible against the other issues.

### S4. The 2023 grid vintage is decisive in WY/UT and NM, so add a forward-looking A sensitivity (Q5)
- In ERCOT and PJM, holding the grid at 2023 was a small pro-BTM choice. In WACM and PACE it may decide the verdict.
- Known or likely changes in 2027–2046:
  - PACE: Naughton gas conversion, Dave Johnston retirement dates [MEMORY].
  - WACM: Craig units 1–3 and Hayden retirements, and DOE 202(c) orders delaying some [MEMORY]. Laramie River has no announced retirement [MEMORY].
  - Policy pushes in opposite directions. New Mexico's Energy Transition Act requires zero-carbon IOU supply by 2045 [MEMORY]. Cleanview notes NM HB93 lets microgrids bypass the ETA [OPENED]. Wyoming and Utah have laws resisting coal retirement [MEMORY].
- **Fix.** Add the Cambium 2024 LRMER for every region; it is cheap. The local workbook already contains all 18 GEAs, and the county mapping is now verified [OPENED]:

  | Site county | Cambium GEA |
  |---|---|
  | Laramie WY | WestConnect_North |
  | Millard UT | NorthernGrid_South |
  | Doña Ana NM, El Paso TX | WestConnect_South |
  | Shelby TN | SERTP |
  | DeSoto MS | MISO_South |
  | Taylor, Shackelford TX | ERCOT |
  | Armstrong TX | SPP_South |
  | Licking OH, Loudoun VA, Cumberland NJ, Indiana PA | PJM_East |

- Optionally add a Cambium mid-case **average** emission rate path. The local workbook appears to hold marginal metrics only, so this would need the Scenario Viewer [inferred from sheet names; not confirmed].
- Label everything pre-OBBBA, as in the main analysis. For coal-heavy regions, also run an "announced retirements" A built from the eGRID plant file minus retiring units, with an explicit replacement-mix assumption. Show that this cuts both ways: new load can also delay coal retirements.

### S6. Regional transmission losses (Q5)
The flat 3% transmission-only loss on the grid side, against 1% for BTM, is adequate as the primary. The regional variation is second-order next to M3 and M8: plausibly 2–5% across these regions [MEMORY], against the 2–5% range already in the main MC. Long rural transmission in WACM and PACE would raise the grid's loss and favour BTM slightly. The interstate exports in M3 (Laramie River, Intermountain) carry their losses to other consumers. Option: use EIA state-level electricity balance data (losses as a share of supply) as a regional sensitivity [MEMORY that the state tables report losses]. Keep the MC range U(2%, 5%) in the per-region MC (S1).

### S5. Rename the asymmetric-rule text and fix the §6 judgment-call wording
- §2 says the BA is "conservative toward BTM" in the Mountain West, which is correct.
- §6 says Uinta is "the conservative choice toward the grid", which, under the plan's own convention, means anti-BTM.
- Use one phrase throughout, "favours BTM / favours grid", and tag every judgment call with its direction in a table.

---

## OPTIONAL

- **O1. Marginal-molecule pairing (consequential).** Permian gas is associated gas: new demand does not raise Permian output, it displaces Permian gas that would have gone elsewhere, and the marginal production response is plausibly Haynesville [MEMORY; this argument is already a caveat in METHODS]. A "Haynesville L for BTM and B in all regions" case would be the most BTM-favourable consequential bracket. It is also the right foil for the Uinta and Permian pairings, which are attributional.
- **O2. Regionalized B.** Keep B as the H-class 6.2 for comparability; it is the "even if it's all gas" reference. As an optional sensitivity, add an ambient- and altitude-adjusted B: Cheyenne is about 1,850 m and Delta, UT about 1,400 m [MEMORY], and West Texas and El Paso are hot. Apply the same adjustment to the BTM turbines, since they derate too. Raising B would make the test more lenient toward BTM where B binds. Do **not** regionalize B to "what the utility would actually build" (for example peakers or gas-converted steam). That reference becomes gameable, and the LRMER already plays that role.
- **O3. Cleanview projects not covered:** Meta Bowling Green, OH (350 MW, Williams) and Fermi Matador (see M1).
- **O4. Note scale.** Jade at 10 GW approved and Joule at 12 GW are each a large share of regional gas supply. This strengthens the case that supply would be pipeline-mixed and argues against basin-local pairing for the largest sites.

---

## Answers to the six questions, in brief

1. **Grid-factor rule.** Not defensible as drafted. It is not consistently BTM-conservative: NM and TVA take the lower candidate, while WY, UT and MISO take the higher. Neither BA nor subregion is uniformly closer to consumption. WACM's production includes MROW-assigned coal, NWPP is BPA hydro, SRTV includes LG&E-KU, and EPE omits its Palo Verde share. EIA-930 publishes consumption (load) CO2 intensities per BA via MRIO [OPENED]. Use that as the single primary, with BA production and subregion as the bracket. That is the least gameable choice. (M3)
2. **Basin pairings.**
   - Appalachia and Haynesville: fine.
   - Permian TX range: mixes basin-wide and state values (skewed pro-BTM).
   - NM/El Paso: the NM-state intensity is applied to a Texas site, which favours BTM. Use basin-wide.
   - Wyoming: DJ central is the most BTM-favourable option and is likely not the physical supply. Use a Rockies mix.
   - Utah: Uinta violates the stated rule and is physically too small to supply a 4–12 GW campus.
   - Matched pairing inflates A in high-L basins and deflates it in low-L basins. Keep both pairings as the bracket.
   - B should use local L in all pairings. (M4, M5, S2, S3, M9)
3. **Tie bands.** Not acceptable for high-L or coal-heavy regions; the error runs in both directions. Re-run the MC per region with basin L and CMM draws. It is cheap. (S1)
4. **Two-condition test in coal regions.** Keep it as the pre-registered "worse" test, but it collapses to "above A" when A > B, which the §7 text gets backwards. Add the four-state classification and pre-register the "Between" framing. Do not regionalize B to a realistic local build; use LRMER for that role. An ambient/altitude-adjusted B is optional. (M6, M7, O2)
5. **Missing pieces.**
   - Basin-specific coal-mine CH4: about 52 kg/MWh at national factors in WACM, likely overstated for PRB.
   - Coal supply-chain CO2: a latent omission in the main analysis too, about 3 kg/MWh in ERCOT/PJM.
   - Transmission increment for off-basin sites.
   - Regional T&D: keep the flat 3%; regional variation is second-order and already inside the MC's 2–5% range.
   - Consumption-based imports (M3).
   - A post-retirement or LRMER view of A: the counties are mapped and the data are on disk.
   (M8, S3, S4, S6)
6. **§7 predictions.**
   - Fix the binding-reference error and the "tens of kg/MWh" magnitude: it is 166–254 kg/MWh at GWP100 for Uinta vs national.
   - Add Southaven and the Panhandle.
   - State A-vs-B ordering per region.
   - State the EPE exception to "can only flip one way".
   - Add per-cell predictions for the efficient cases. (M6)

---

## Verification log
- [OPENED] eGRID2023 rev2 PLNT23: plant BA and subregion for Laramie, Platte, Campbell, Converse (WY); Millard, Emery, Juab (UT); DeSoto (MS); Shelby (TN); Doña Ana (NM); El Paso, Taylor, Shackelford, Potter, Randall (TX). BA-by-subregion decomposition for WACM, PACE, TVA, EPE, PNM, MISO, ERCO, PJM, and BA composition of SRTV, RMPA, NWPP, AZNM, MROW, SRMV. The plant-sum CO2e/generation reproduces the BA rates in `grid_inputs.json` (854, 644, 292, 459, 179, 448, 334, 326). Script: `/private/tmp/claude-501/-Users-hausfath-Desktop-Climate-Science-The-Climate-Brink/b6426cdf-39dc-4a8b-80be-b965c2c3cd9b/scratchpad/ba_sr.py`.
- [OPENED] Cambium24_Workbook.xlsx: GEA list (18), County Mapping rows for 13 site counties.
- [OPENED] Cleanview page: project counties and sites [quoted Cleanview detail removed at Cleanview's request].
- [OPENED] EIA-930 about page: consumption (load) CO2 intensity via MRIO. Its footnote reference was not opened.
- [BASINS.md] All basin L values and the MacKay boe shares. I did not re-open the primary papers; the tags are the subagent's.
- [MEMORY, unverified] Colossus 2 load location; pipeline geography (Kern River, REX, Cheyenne Hub, EPNG/Waha); Tallgrass CCS; EPE's Palo Verde share; PRB vs underground CMM magnitudes; EIA-923 and GHGI annex data fields; coal retirement dates and DOE 202(c) orders; NM ETA targets; Alvarez segment split; NETL coal supply-chain CO2; site altitudes; Open Grid Emissions / gridemissions coverage.
