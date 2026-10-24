# Domain review of PLAN.md v1.1 (gas methane and power-sector accounting)

Reviewer: domain subagent (natural-gas CH4, combustion EFs, grid average/marginal factors). Date: 2026-10-24.
Scope: PLAN.md v1.1 including the "Notes added while the reviews ran" section, `sources/lit_scan/FINDINGS.md`, the Irzak transcript, AP-42 3.2,
the Cambium 2024 workbook in `data/cambium/`, and the earlier gas LCA `params.py`/`bottom_up.py`. PLAN.md was not edited.

Source tags used below: **[opened]** = I read the primary text or data file in this session; **[lit-scan]** = taken from FINDINGS.md, where the
scan agent says it opened the source but I did not re-open it; **[memory]** = from my own knowledge, not checked in this session, so treat as
unverified until someone opens the source. **[my arithmetic]** = computed here from the stated inputs.

---

## Bottom line

The plan is well built. Its central logic is right: methane can only change the **ranking** where combustion CO2 is close to the grid reference,
and that happens only for the efficient BTM options (combined cycle, SOFC). Recips and simple-cycle turbines are already worse on combustion
CO2 alone. That pre-registered expectation is now confirmed by the lit-scan numbers (EIA IC 8,853 Btu/kWh → ~470 kg CO2/MWh vs eGRID ERCT
334 kg). Five problems would still undermine the result or embarrass the post:

1. The emissions function has **no upstream CO2 term**, so V1 will fail and BTM and Cambium "combined" numbers will be on different bases.
2. **"Higher of average and LRMER" does no work.** Cambium 2024 LRMER is far below the eGRID average in every relevant region and scenario,
   so the rule always returns the average. The more important grid reference, "new NGCC built for the load", is missing.
3. **Leak-rate bases are mixed** (gross vs sales vs delivered; six-region vs national; grid vs BTM in the same basin).
4. Sherwin 2.43% is labelled "national". It is a six-region, oil-weighted average. Irzak's Permian 4% is now the high end of recent estimates.
5. The one comparison where methane could flip the ranking (BTM NGCC or SOFC vs the ERCOT average) will land within about ±10%. Inside that
   band the sign depends on conventions, so the tie-break rules have to be fixed **before** running.

---

## MUST-FIX

### M1. Add an upstream CO2 term (processing, lease/plant/pipeline fuel, flaring, acid-gas venting)
- §3's E has combustion CO2 + CH4 terms + N2O and nothing for upstream CO2. NETL and Cambium both include it.
- Size check [my arithmetic]. NGCC-F at 53.6% HHV gives HR 6.366 MMBtu/MWh and 337.8 kg CO2/MWh. The NETL upstream CH4 term is 21.0 g/kWh
  (`params.py`, from the earlier reproduction [opened]). Combustion CH4+N2O is ~0.4. Total ≈ 359 against NETL's 394.7, a gap of ~36 kg/MWh
  (9%). V1 as written (±3%) **cannot pass** without either this term or tuning.
- Independent corroboration [opened, Cambium24_Workbook.xlsx, Data - Annual]: precombustion CO2 is ~10% of combustion CO2 in gas-dominated
  regions (ERCOT 2025 Mid-case: 41.5 vs 409 kg/MWh). For gas that is ≈5.3 kg CO2/MMBtu, consistent with the ~5.6 kg/MMBtu NETL residual.
- Action: add `m_upCO2` (kg CO2/MMBtu delivered). Derive it from the V1 reproduction rather than hardcoding it, and apply it **identically** to
  BTM gas and to grid gas. Run a Permian-specific sensitivity, since flaring and AGR CO2 are higher there. That sensitivity is directional
  only: I have no verified Permian number.

### M2. Replace the grid-reference rule; add "new NGCC on the grid" as the primary ranking reference
Cambium 2024 values, extracted here [opened; my arithmetic: undiscounted 2027–2046 mean, linear interpolation between 5-yr points, end-use,
combustion + precombustion, AR6 GWP100]:

| Region | Mid-case | High RE cost + Low NG | High Demand Growth | Combustion CO2 only (Mid) |
|---|---|---|---|---|
| ERCOT | 147 | 162 | 167 | 111 |
| PJM East | 272 | 298 | 279 | 202 |
| PJM West | 198 | 218 | 200 | 149 |

(kg CO2e/MWh.) The eGRID2023 averages are combustion only and contain no upstream: ERCT 334, US 350 kg CO2e/MWh [lit-scan]. Every LRMER is
lower, so "higher of average and LRMER" **always** returns the average. The rule looks conservative but does nothing, and a reader will
assume LRMER mattered. ERCOT Mid-case combustion CO2 falls from 409 (2025) to 151 (2030) to 53 (2035) kg/MWh [opened]. That is not a
credible path for a market now adding gas for data-center load.

Recommended grid references (show all three; pre-register which one decides the ranking):
- **(i) Average:** latest eGRID (2023 rev2) plus upstream CH4 **and CO2** on the gas share; plus coal-mine methane on the coal share (M5);
  plus **transmission-only** losses. A GW-scale data center connects at 138–345 kV, so distribution losses do not apply. US transmission
  losses are ~2–3% [memory]. Keep ~5% T&D as a sensitivity. Use EIA-930 2025 BA-level CO2 [lit-scan says available] as a more current check
  on eGRID2023. EIA-930 also gives PJM as a BA. eGRID publishes subregions only [lit-scan], and PJM spans several of them (RFCE/RFCW/SRVC) [memory].
- **(ii) "Grid + the generation the load induces" = new utility NGCC:** H/F-class at ~6.2–6.4 MMBtu/MWh HHV [memory; EIA CC tested
  7,535 is the fleet, lit-scan], same gas, same L, same upstream terms, plus transmission losses. This is what utilities are actually
  building for large-load growth. The lit scan's Meta Hyperion/Entergy CCGTs are an example [lit-scan, UNVERIFIED there]. It is the
  **apples-to-apples test of the BTM prime-mover penalty**: heat rate, slip, redundancy and part load. I would make it the primary ranking
  reference: it is defensible to a critic and needs no contested grid model.
- **(iii) Short-run marginal ceiling:** eGRID non-baseload (ERCT 1,248 lb ≈ 566 kg; US 1,379 lb ≈ 626 kg [lit-scan]) or EPA AVERT
  [memory: AVERT is EPA's marginal-displacement tool]. Use it only for the first ~3–5 years, before induced build arrives (Cambium's own
  guidance text says the same [opened]). Label it coal-inclusive and an upper bound.
- **Cambium LRMER:** keep it, labelled "policy-optimistic lower bound (pre-OBBBA)". See M3.

Consequence to pre-register: under reference (iii), **BTM recips on low-leak gas could beat the grid on GWP100** (~470 + methane vs ~566 +
upstream). Under the conservative-toward-BTM rule, (iii) is the "highest defensible" grid number. The plan must state in advance why (iii)
does not decide the headline: a 20-year, GW-scale, flat load induces build. Otherwise a critic will say the author picked the reference that
gave the answer he wanted.

### M3. Cambium vintage handling (coordinator's question)
- Facts [opened, workbook "Scenario Definitions" and "Description and Guidance"]:
  - Policies are "as they existed in August 2024".
  - NREL says: "not recommended to use Cambium data for estimating current conditions ... If analysts are predominately interested in the near
    term (i.e., within the 2020s), they would likely be better served by drawing from recent empirical observations".
  - Data come at 5-year steps (2025, 2030, ...).
  - "Location: End-use" is the default. The busbar option divides out a "Distribution Loss Rate", so **end-use values already include
    distribution losses. Do not add T&D on top of Cambium end-use** (§5 currently would). Use busbar × (1 + transmission loss), or end-use
    alone labelled as conservative toward BTM.
- Its precombustion CH4 runs ~7.5 kg CH4 per t of combustion CO2 in gas-dominated years [opened]. That is ≈0.40 kg CH4/MMBtu, ≈2.1–2.3% of
  delivered CH4 [my arithmetic, using 17.75–19.0 kg CH4/MMBtu]. Cambium's implied leak rate is therefore already close to 2.43%, and
  re-basing it is a small adjustment, not a correction. Re-base by scaling only the precombustion-CH4 component.
- GWP: the workbook offers AR5 and AR6 sets [opened]. Use AR6 100-yr and 20-yr from the GWP tab.
- Handling:
  - (a) Show the Mid-case / High RE cost + Low NG / High Demand Growth bracket, not one scenario. NREL's own guidance asks for ranges
    [opened].
  - (b) Do not call High RE + Low NG a "post-OBBBA proxy". It still has IRA credits and is still well below the average.
  - (c) Before publishing, check scenarioviewer.nlr.gov / data.nlr.gov for a Cambium 2025 or a 2025 Standard Scenarios release with
    post-OBBBA policy [the lit scan found none; I did not check].
  - (d) Put "Cambium 2024, August-2024 policy" in any caption that shows it.
  - (e) Use the 2027 start with an undiscounted mean as primary. The workbook defaults to a 3% real discount rate, which weights the
    high-emission early years more; show it as a variant.

### M4. Leak-rate definitions and pairing
- **Denominators.** Alvarez (2.3%) and Zhang (3.7%) are % of gross production [lit-scan], and Chen (9.4%) is % of gross gas production
  [lit-scan]. Sherwin's is "covered natural gas production" [opened]. MiQ and EDF/MethaneSAT are per sales/produced-and-sold gas [lit-scan].
  NETL's 0.55% is kg CH4 per kg NG **delivered** [opened, params.py]. The plan's `c × L/(1−L)` assumes delivered CH4 = (1−L) × produced
  CH4. It ignores lease/plant/pipeline fuel and processing shrink, which are several percent of gross withdrawals [memory, EIA natural gas
  balance]. Define L on each study's own basis. Convert with an explicit gross-to-delivered CH4 ratio from the EIA balance, and state the
  ratio: `m_up = c_CH4 × L × (P_CH4 / D_CH4)`. Expect a ~5–10% change in the upstream term [memory-based estimate], larger than the
  L/(1−L) correction itself.
- **Sherwin 2.43% is not national.** The article text: "six regions in the USA, comprising 52% of onshore oil and 29% of gas production"
  [opened]. The sample is oil-weighted: it covers half of onshore oil but under a third of gas. The issue is production weighting, not omission. The 0.71% "high-productivity, gas-rich region" is probably Appalachia [inference, not checked], but gas-rich low-loss supply (Appalachia ~0.5% [lit-scan, EDF/AMI blog], Haynesville) is underweighted relative to its share of US dry gas. Relabel it "measured,
  six-region (oil-weighted) average". Use Alvarez 2.3% (2015 data) [lit-scan] as the national anchor, with a production-weighted basin
  composite as a check. The grid-gas "national" L should not be the Sherwin number without that caveat.
- **Same-basin pairing for ERCOT.** §5 puts grid gas at 2.43% while BTM is shown up to 4% Permian in the same market. ERCOT grid gas is
  largely Texas gas (Permian, Eagle Ford, Haynesville) [memory]. A BTM plant on Permian gas compared with a grid on cleaner "national" gas
  tilts **against** BTM, which breaks the plan's own conservatism rule. Primary ERCOT comparisons should use the same L on both sides. The
  asymmetric version is a sensitivity. The answer to the plan's reviewer question ("one grid line per region?"): yes for display, but the
  grid line must move with L whenever the BTM bar's L differs from the grid gas's plausible supply.

### M5. Coal on the grid side
If upstream CH4 is added to grid gas, add coal-mine methane to the grid's coal share too. Otherwise the accounting is asymmetric, and the
grid is understated, which is not conservative toward BTM. PJM and ERCOT both still burn coal [memory: coal is roughly a mid-teens %
share of generation in each]. Use EPA GHGI CMM / US coal production for an intensity [memory; not verified]. The term is small for ERCOT
and larger for PJM West.

---

## SHOULD-FIX

### S1. Engine slip: W-7 and AP-42 are not independent, and neither describes modern gensets
- Inference [my arithmetic + opened AP-42 + lit-scan Vaughn abstract]:
  - AP-42 4SLB CH4 is 1.25 lb/MMBtu = 0.567 kg [opened, AP-42 3.2 Table 3.2-2, rating C, dated 7/00]. Vaughn et al. 2021 found 4SLB 8%
    below AP-42 [lit-scan], and 0.567 × 0.92 = 0.522 = W-7. Their 4SRB was 43% of AP-42, and 0.229 lb × 0.4536 × 0.43 = 0.045 = W-7.
  - 2SLB: AP-42 1.45 lb = 0.658 = W-7.
  - So W-7 (2024) is very likely AP-42 scaled by one gas-compressor field study. Confirm in the 89 FR preamble before saying so in print.
    Either way, the "AP-42 cross-check" in §3 is not independent corroboration.
- Both are populations of **pipeline compressor** engines. AP-42 says "Most natural gas-fired reciprocating engines are used in the natural
  gas industry at pipeline compressor and storage stations" [opened]. They are not the 60-Hz high-efficiency gensets being ordered (Cat
  G3520K, Jenbacher J620/J624, Wärtsilä SG) [lit-scan, Cleanview]. The only genset data in hand is the Cat G3516 sheet, 2.3–3.0% of fuel
  CH4 not-to-exceed, older model [lit-scan]. ICCT-cited marine LBSI is 1.3–2.6% [opened, ICCT FUMES]. These bracket W-7's ~2.9%, so keep
  W-7 as central and add a 1.5–4% range. Do not present W-7 as "the EPA average at full capacity", as Irzak does. AP-42's footnote says
  factors are "for engines at all loads" [opened], so the plan's correction of her is right.
- **Oxidation catalysts.** AP-42 "uncontrolled" for CH4 means "no oxidation control" [opened]. Data-center gensets will mostly have
  SCR + CO/HCHO oxidation catalysts for NSPS JJJJ / NESHAP ZZZZ compliance [memory]. Standard Pt/Pd catalysts at lean-burn exhaust
  temperatures (~400–450 °C [memory]) oxidize little CH4, so treat the reduction as ~0. A "with oxidation catalyst" BTM case should not be
  given a CH4 credit unless a vendor guarantee is found.
- **Add a 4SRB (rich-burn + NSCR) small-genset case.** Meta El Paso / Enchanted Rock uses 813 × 450 kW Generac units [lit-scan, Cleanview].
  Small natural-gas gensets of that class are typically rich-burn with three-way catalysts [memory, unverified for this project]. W-7 slip
  for them is 0.045, low, but the heat rate is poor (~11–12.5 HHV [memory]). This case shows "low slip ≠ low emissions".

### S2. Part load and redundancy: give a central bracket, and compound the two effects
- Load dependence evidence [opened, ICCT FUMES ES]: real-sailing LPDF slip is ~2% at ≥75% load, ~2.5% at ~50% load, and 4–7% at ≤25% load,
  from marine dual-fuel engines. That is a different combustion system from land spark-ignited lean-burn units (flag this). The Cat G3516
  sheet is non-monotonic (3.0/2.3/2.4% at 100/75/50%) [lit-scan].
- Realistic island-mode dispatch:
  - Recip plants have many small units, from tens to hundreds (Frontier: 620 Jenbacher units for 2.58 GW [lit-scan]). N+1/N+2 spinning
    reserve then costs only a few % of load per unit; e.g. N=40, N+2 → ~95% load.
  - AI training load is roughly flat at the hour scale but has fast sub-second swings, usually handled with BESS [memory].
  - So the central part-load case is **~85–90% unit load**: slip multiplier ~1.0–1.3, HR penalty ~1–3% [memory: genset part-load curves].
  - A "solar-following / 50% load" case gives slip ×1.5–2 and HR +5–8% [ICCT curve for slip; memory for HR]. Label it a stress case.
- Per-MWh slip = HR × slip-per-MMBtu, so both penalties multiply. Make sure the code applies the slip multiplier to the part-load HR, not the
  full-load HR.
- Startup/shutdown: Hajny et al. 2019 measured one NGCC during startup at ~440 g CH4/MMBtu and a 2.5% loss rate [lit-scan, abstract]. Add
  a turbine "×10 AP-42" sensitivity. It will not change any ranking, since 0.04 kg/MMBtu is still ~10× below recips, and showing it closes
  off the "turbines slip too" objection.

### S3. Prime-mover heat rates (HHV) I would use
These are my values. Vendor efficiencies are [memory] and LHV, converted at 1.108; verify each from a data sheet before the case table is
frozen.

| Case | Central HR (MMBtu/MWh HHV, net) | Range | Notes |
|---|---|---|---|
| Recip 4SLB, modern 4–10 MW (J620/J624, G3520K) | 8.4 | 7.6–8.85 | ~45–46% LHV electrical [memory], +1–2% parasitics (radiators). EIA IC tested 8,853 [lit-scan] is the fleet ceiling. Large Wärtsilä SG ~48–50% LHV → ~7.6–7.9 [memory] |
| Recip 4SRB small (450 kW class) | 11.5 | 10.5–12.5 | [memory]; low slip |
| Aeroderivative / mobile SC (TM2500, LM2500XPRESS, LM6000, Titan 130/350) | 10.0 | 9.3–11.0 | LM6000 ~40% LHV, TM2500/Titan 130 ~35–37% LHV [memory]. EIA GT 10,975 [lit-scan] as upper. Add a high-ambient derate (+3–5% in Texas summer [memory]) and fuel-gas compression parasitics (1–2% [memory]) |
| BTM combined cycle (campus) | 6.6 | 6.3–7.2 | Island operation with N+1 runs below rated output; smaller aero-based CC is ~7.0 [memory] |
| SOFC (Bloom) | 6.8 | 6.3–7.5 | ~54–60% LHV beginning of life [memory, vendor claim]; lifetime average is worse with stack degradation. Cleanview puts Bloom at 14% of identified BTM capacity [lit-scan], so make it a **main case, not optional** |
| Grid NGCC (new H/F) | 6.3 | 6.2–6.6 | Reference (ii) |

### S4. Associated-gas allocation and the marginal molecule in the Permian (a likely expert objection)
- Basin loss rates divide **all** oil-and-gas CH4 by gas production. In the Permian, an oil-driven basin, the gas share of energy output is
  about half [memory: ~6+ Mb/d oil and ~25–28 Bcf/d gas]. Energy allocation would put roughly 45% of upstream CH4 on gas. On that basis
  a 3.2% Permian loss becomes ~1.4% attributable to gas [my arithmetic on memory inputs].
- Consequentially, extra Texas gas demand may absorb associated gas that is otherwise flared or sold at negative Waha prices [memory]. The
  incremental wellhead CH4 from that demand could then be small, while gathering/processing throughput emissions still scale with it.
- The plan's conservative-toward-BTM rule implies running an allocation sensitivity. It affects grid gas from the same basin equally (if M4
  pairing is adopted), so it changes the gap, not the ranking. Say so explicitly. This is the main way an oil-and-gas LCA person will
  attack a "Permian 4%" framing.

### S5. Permian and national leak cases: proposed set
- 0.2% "best operators": per MiQ the grade thresholds are upstream-only (A ≤0.05%, C ≤0.20%) and per sales gas [lit-scan, MiQ v1.1].
  Irzak's "0.2%" is a production-segment number. **The full-chain best case is higher.** Use ~0.5% (Appalachia AMI 0.52% [lit-scan]; NETL
  inventory 0.55% [opened, params]) as the realistic floor. Keep 0.2% only as "Irzak's best-operator wellhead value, excludes midstream".
- National central: Alvarez 2.3% [lit-scan]. Measured six-region: Sherwin 2.43% [opened]. Inventory: NETL 0.55%.
- Permian central **3.1–3.3%**, range 2.1–3.7%:
  - Bridger 2024 basin 3.13% (TX 3.6%, NM 2.1%) [lit-scan; ES&T 2026].
  - TROPOMI 2019–2023 intensity falling from 5.2% to 3.2% [lit-scan; ES&T 2026].
  - MethaneSAT 2024–25: TX 3.1%, NM 1.2%. That is an advocacy page and not peer reviewed [lit-scan].
  - Zhang 2020's 3.7% is 2018–19 data; Chen 2022's 9.4% is NM only, 2018–20 [lit-scan].
- Irzak's 4% is therefore at the **high end** of current whole-basin estimates. Keep it as "Frost's stated value", not as "the Permian".
  Sherwin's own range runs up to 9.77% for "a rapidly expanding, oil-focused region" [opened]. If a "highest published" tail is wanted, use
  that, labelled as the regional high in a specific campaign.

### S6. Unburned-carbon consistency
Table C-1's 53.06 assumes complete oxidation, while AP-42's CO2 footnote assumes 99.5% [opened]. With ~2.9% of fuel CH4 slipping, ~2.5–3% of
fuel carbon never becomes CO2. Subtract `EF_CO2 × slip_fraction × (C in CH4 / total C)`: ~1.4 kg CO2/MMBtu, ~12 kg/MWh for a recip
[my arithmetic]. It is small, but it runs in BTM's favour, so the conservatism rule requires it.

### S7. V2 (Frost) decomposition: sound solve, over-specific split
- The two-equation solve checks [my arithmetic]: CH4 = 1.567 kg/MMBtu, a 45% CH4 share at GWP100, CF×HR = 5.97 MMBtu/MWh. It is
  **proportional to the assumed CO2 factor**: x = 0.0295 × (CO2 per MMBtu). If Frost's 380 includes ~5.5 kg/MMBtu of upstream CO2 (M1), x
  rises to ~1.73 kg/MMBtu (~9.7% of delivered CH4).
- "7.5%" vs the implied 8.8% reconciles **partly** through denominators [my arithmetic]. 7.5% of gross is ~7.8–8.1% of delivered, depending
  on how the upstream share is split. Pure-methane c_CH4 (19.0 kg/MMBtu) gives 8.2%. Present the result as a range.
- The 8.8% − 2.9% split assumes all 50 GW are 4SLB recips. Cleanview's identified equipment is ~65% turbines and 14% Bloom [lit-scan]. With
  a ~35% recip share, fleet slip is ~1%, and the implied upstream + facility residual becomes ~7.8%, about double her stated 4%. Show the
  residual as a **2-D surface (recip share × slip)** rather than a single "5.9%". The defensible statement is that Frost's numbers are
  consistent with a recip-heavy fleet and a high facility-leak assumption, and that the split cannot be identified from the episode.
- Context checks for the write-up:
  - 50 GW for 18 months against ~2 GW operating mid-2026 and ~3 GW by end-2026 [lit-scan, Cleanview]. 380 Mt is "per 18 months of full
    operation of 50 GW" (~250 Mt/yr), not emissions "in the next 18 months".
  - Her "15% of US grid emissions" for the preventable ~190 Mt does not reconcile cleanly. Against ~1.5 Gt/yr US power CO2 [memory] it is
    ~13% if the 18-month total is compared with one year, or ~8% if annualized. Flag rather than assert.
  - "35 reciprocating engines" for 1 GW implies ~29 MW units. No gas recip is that large; the largest are ~19 MW [memory]. She may be
    thinking of xAI's ~35 turbines [lit-scan]. A recip GW needs 50–250 units, which actually strengthens her facility-leak point.
    Optional to mention.

### S8. FaIR: hold the grid path constant **and** run a declining one
Holding grid intensity flat for 20 years is conservative toward BTM, so keep it. A critic will still say the comparison freezes the grid.
Add a path using the eGRID/EIA-930 2025 value declining to the Cambium High-RE-cost/Low-NG trajectory, and report the BTM/grid ΔT ratio
for both.

---

## OPTIONAL

- O1. `c_CH4`: "High-resolution national mapping of natural gas composition substantially updates methane leakage impacts" (Nature-family,
  Nov 2025) appeared in the "Similar content" list on the Sherwin page [opened the list entry only; paper not opened, authors unknown].
  Worth checking for a delivered-gas CH4 fraction by region.
- O2. "Permian wet gas" sensitivity: only relevant if a project burns unprocessed field gas. Pipeline residue gas is ~93–96% CH4 regardless
  of basin [memory]. Otherwise drop it, or rename it "field-gas BTM".
- O3. eGRID CO2e GWP basis is unresolved [lit-scan]. It is immaterial: CO2e and CO2 differ by 0.5% (770.9 vs 767.2 lb). Say so and move on.
- O4. Crankcase blow-by (open breathers), gas-expansion starters, ESD/blowdowns and pigging on the lateral are not in W-7 exhaust factors
  [memory]. Lump them into `m_fac` with a 0–0.5% range, as planned, and name them so readers see they were considered. More units (N+2 on
  hundreds of recips) means more connections, which supports Irzak's facility-leak argument qualitatively.
- O5. Define "BTM" precisely: islanded/off-grid vs grid-parallel co-located. Grid-parallel plants can run at efficient load and lean on
  grid reserves, so the redundancy penalty applies to islanded plants only. Bridge-then-backup is already a listed caveat; keep it
  prominent.
- O6. HHV/LHV 1.108 is fine for pipeline gas (pure CH4 ~1.109 [memory]). EIA heat rates are HHV by convention, but the pages the scan
  opened do not state it [lit-scan]. Cite the EIA glossary, or state the assumption.

---

## Answers to the six questions (short form)

1. **Emissions function:** Algebra is fine in form. Missing: upstream CO2 (M1, must-fix), denominator conversion (M4), unburned-carbon
   adjustment (S6), CMM on the grid side (M5), and facility non-exhaust terms (O4). Flaring CH4 from inefficient/unlit flares is already
   inside measurement-based L (aerial/satellite see it); flaring CO2 is not, and belongs in M1.
2. **Cases:** Make Bloom SOFC a main case and add 4SRB small gensets. Central recip ~8.4 HHV with EIA 8,853 as ceiling; aero/SC 9.3–11.0
   plus ambient and compression adders; BTM CC 6.6. Part-load central ~85–90% unit load with slip ×1.0–1.3 compounding with the HR
   penalty. The only measured load curve is marine (ICCT); label it as such.
3. **Leak cases:** Replace 0.2% (wellhead-only) with ~0.5% full-chain best-case. National = Alvarez 2.3%; Sherwin 2.43% relabelled as
   six-region. Permian central 3.1–3.3%, range 2.1–3.7%; 4% = Frost's value; 9.77% as the campaign tail.
4. **Grid:** "Higher of average and LRMER" is degenerate (LRMER always lower). Use three references: the average with symmetric upstream
   and transmission-only losses; new utility NGCC as the primary ranking test; SRMER as an early-years ceiling. Cambium is a labelled
   pre-OBBBA lower bound. Don't stack T&D on Cambium end-use. Pair L by basin.
5. **V2:** The solve is sound. The upstream/slip split is not identified. Present a surface and a range and fix the 18-month framing.
6. **Embarrassment risks:** (a) calling Sherwin "national"; (b) treating Irzak's 4% as the Permian value; (c) a reference rule that silently
   reduces to eGRID average; (d) a near-tie result (below) reported as a ranking change or as "no change" without a pre-registered
   tie-break; (e) no oil/gas allocation caveat; (f) quoting 380 Mt as "the next 18 months".

## Pre-register this tie-break now
Illustrative arithmetic [my arithmetic; ERCOT gas share ~47% of generation and grid gas HR 7.8 are memory]:
- BTM NGCC at 6.4 HR with L = 2.43% and upstream CO2 5.5 kg/MMBtu: ≈ 340 + 35 + 84 + 1 ≈ **460** kg CO2e/MWh.
- ERCOT average with symmetric upstream (gas and coal) and 3% transmission losses: ≈ (334 + ~69 + ~10) × 1.03 ≈ **425**.
- On combustion CO2 only, BTM NGCC (340) is slightly **below** the ERCOT average with losses (~344).

So BTM combined cycle vs the ERCOT average is the one place where methane can flip the ranking, and the margin (~8%) is smaller than the
swing from several open conventions: gross vs delivered L, 3% vs 5% losses, the upstream CO2 value, same-basin vs national L, and the
part-load HR of an islanded CC. Decide these before running and report the outcome as "within convention uncertainty" if |Δ| < ~10%.
Against reference (ii) (grid NGCC), methane never changes the ranking: every BTM option has an equal or worse heat rate plus redundancy,
and recips add slip. That result is robust and should be the backbone of the "build on the grid" argument. The average-grid comparison is
supporting context.
