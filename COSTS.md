# What off-grid gas power costs a data center (quick estimate, 30 Oct 2026)

`scripts/costs.py` writes the outputs to `results/costs/`: `lcoe_main.csv`, `lcoe_sensitivities.csv`, `grid_references.csv`, `bridge_lease.csv` and `lazard_reproduction.csv`. Run it with `python3.13 costs.py` from `scripts/`.

This estimate was not pre-registered or reviewed. Heat rates come from `cases.py`, so the costs and the emissions figures describe the same machines.

## Basis

- "Lifetime average" here is the discounted levelized cost. An undiscounted mean of the yearly costs would be a few dollars higher, because gas rises through the life: the 20-year mean delivered gas price is $5.65 vs $5.08 levelized, about +$5/MWh for engines and turbines.
- Dollars are nominal and levelized flat over a 20-year life from a 2027 start, the same convention as Lazard and a flat PPA price.
- Costs are per MWh delivered to the load, after the 1% on-site loss used in the emissions work.
- Capital is recovered with a fixed charge rate: CRF(after-tax WACC) × (1 − T·PV(depreciation))/(1 − T). It includes interest during construction.
- Financing follows Lazard 2026: 60% debt at 8% and 40% equity at 12%.
  - The central case uses a 25.7% combined tax rate, giving an 8.4% after-tax WACC (Lazard's 40% rate gives 7.7%, because the debt tax shield is larger).
  - Lazard's 40% tax rate is run as a sensitivity.
  - O&M escalates at 2.25% a year (Lazard).
- **Bare plant**: generation sized to the site's peak load and running at the data center load factor (0.80).
- **System**: enough units that P(units available ≥ units needed for peak) ≥ 99.99%. Units are assumed to fail independently, with availability 0.95 for engines and turbines, 0.97 for SOFC modules and 0.92 for CC blocks.
  - This reflects unit size. A 300 MW site needs 82 engines of 4.4 MW for 69 needed, about +19%. It needs 14 turbines of 35 MW for 9 needed, about +56%.

## Validation

The script reproduces Lazard LCOE+ 2026 (v19.0) gas peaking and gas CC from Lazard's own inputs. It uses 30 years, $3.45 flat fuel, 24-month construction, 15-year MACRS and no escalation.

| Row | Lazard | Ours | Error |
|---|---|---|---|
| Gas peaking, low | 144 | 145.5 | +1.0% |
| Gas peaking, high | 276 | 285.6 | +3.5% |
| Gas CC, low | 51 | 48.1 | −5.7% |
| Gas CC, high | 129 | 131.7 | +2.1% |

- The CC-low miss is all in the capital component: Lazard's is $25 and ours is $21.7.
- Lazard solves a levered equity IRR, while we use a WACC fixed-charge rate. Agreement is therefore ±6%, not exact.
- 20-year MACRS and O&M escalation fit worse (−4% to +9%). The central case does escalate O&M at 2.25% a year, which adds about 2–3% relative to the validated specification.

## Inputs (capex in 2026 $/kW overnight: central, low–high)

Capex reflects **current order-book pricing**. Turbine and engine prices have risen sharply as data-center demand has outrun manufacturing capacity:
- Brattle and Sargent & Lundy's draft ERCOT CONE study (Oct 2026) puts an H-frame CT at $1,853/kW overnight (2026$), up from $918/kW in December 2023. It finds "overnight capital costs for an H-class frame CT have increased by $623/kW or 51% in nominal terms" since the 2025 PJM CONE study, with "gas turbines alone … now above $660/kW" ([SAWG summary](https://www.ercot.com/files/docs/2026/10/05/11.-2601007-SAWG-presentation-to-WMS-v1.pdf); [draft report](https://www.ercot.com/files/docs/2026/10/01/3.-SAWG_Oct2026_ERCOT_CONE_Draft_Report.pptx)).
- For the smaller machines data centers actually use, Brattle's Feb 2026 ERCOT workshop says of "smaller frames/aeroderivatives/RICE" that "recent estimates for these approach or exceed $3,000/kW overnight costs" ([deck](https://www.brattle.com/wp-content/uploads/2026/02/ERCOT-CONE-Workshop-Trends-in-Costs-and-Sketch-of-a-2026-ERCOT-CONE-Study.pdf)).
- EIA's AEO2026 cost table (Table 3, [EMM assumptions](https://www.eia.gov/Outlooks/Aeo/assumptions/pdf/EMM_Assumptions.pdf), 2025$) raised simple-cycle costs "about 40%" using the 2025 PJM study. It therefore predates the further 51% rise and is used here as the low case.

| Technology | Capex | FOM $/kW-yr | VOM $/MWh | HR (HHV) | Sources |
|---|---|---|---|---|---|
| Recip engines | 3,000 (2,470–3,520) | 43.7 | 7.1 | 8.40 | Central: Brattle "approach or exceed $3,000/kW". Low: EIA AEO2023 ICE ($2,240 in 2022$), pre-boom. High: AEO2026 aero × 1.51 (the post-PJM-study escalation). O&M from AEO2023 ICE, since AEO2026 dropped the ICE row. |
| Simple-cycle turbines | 3,000 (2,330–3,520) | 10.2 | 6.1 | 9.80 | Central: Brattle. Low: AEO2026 aeroderivative CT ($2,275 in 2025$). High: AEO2026 aero × 1.51. O&M from AEO2026 (9.99 / 5.97 in 2025$). |
| Fuel cells (Bloom SOFC) | 5,700 (3,000–8,490) | 38.7 + stack replacement of 15% of capex in years 5/10/15 | 0.7 | 6.40 | Central: AEP's "$4 billion, 702-MW Bloom Energy fuel cell plant" for Google ([POWER, Oct 2026](https://www.powermag.com/aep-plans-4-billion-fuel-cell-power-plant-for-google-signs-up-to-1-6-gw-mainspring-generator-deal/)), our division. High: AEO2026 fuel cell total overnight ($8,287 in 2025$). Low: ~$3,000 (**unverified** analyst figure, and an upper reading of AEP's $2.65B option). The stack assumption is ours. |
| CC (on site) | 2,400 (2,100–2,600) | 20 | 4.0 | 6.60 | Lazard 2026 CC range tops at $2,100, plus its "$2,400/kW – $2,600/kW … market quotes for CCGT projects … post-2028 COD" ([Lazard LCOE+ 2026](https://www.lazard.com/media/kcfconhf/lazards-lcoeplus_vf.pdf)). |

Notes on the inputs:
- EIA values are inflated to 2026$ at an assumed 2.5% a year.
- Construction periods are 18 months for engines, 30 for turbines, 12 for SOFC and 36 for CC.
- **Brattle's carrying cost is higher.** Its 50-month development timeline, with turbines reserved years ahead, makes installed cost 1.28× overnight ($2,368 vs $1,853). That is run as a sensitivity.
- **Property tax and insurance are left out of FOM.** Brattle's ERCOT CT FOM is "$52/kW-yr", including property tax, insurance and firm gas, against AEO2026's $7–10. A 1.5%-of-capex-a-year sensitivity covers this.
- **Machines running today mostly paid pre-boom prices.** They were ordered in 2023–25, so the low-capex column is the better guide to their cost. The central case is what a new order costs now.

**Gas, delivered, nominal.**
- Henry Hub uses the NYMEX Cal-2027 strip of $3.003 and the Cal-2028 strip of $3.635 (settles of 26 Oct 2026, NRG daily market update).
- From 2028 to 2032 the price blends linearly into the [AEO2025 Reference](https://www.eia.gov/outlooks/archive/aeo25/excel/aeotab13.xlsx) nominal path, which it follows from 2032.
- A $0.33/MMBtu delivered adder is applied: EIA STEO Oct 2026 power-sector gas cost minus Henry Hub, averaged over 2025–27.
- The levelized delivered price is $5.08, because AEO2025 rises to ~$7–8 nominal in the 2040s.
- In both big off-grid regions (Permian, and Appalachia with TETCO M2 2027 basis about −$0.6 to −0.85 in Aegis and company hedge data), gas sells below Henry Hub. The central fuel case is therefore high for those sites, and the Waha case shows the size of the effect.
- Gas cases:
  - **Strip, then inflation only**: $4.46 levelized.
  - **AEO2026** (the "Counterfactual Baseline"): $6.14.
  - **Waha**: Aegis basis quotes for 2027–28 of −$1.57 and −$2.03, converging to an assumed −$0.50 by 2031; $3.99.

## Results, 300 MW site (levelized nominal $/MWh delivered)

| Technology | Bare plant | System (N+k) | Capex low–high (system) | Main swing factors (system) |
|---|---|---|---|---|
| Recip engines | 114 | **126** | 114–137 | Waha gas −9; AEO2026 +9; Brattle carrying cost +13; property tax and insurance +9; batteries +8; 5-year write-off +80 |
| Simple-cycle turbines | 117 | **150** | 130–165 | Spares +33; Waha −11; carrying cost +14; property tax and insurance +12; 5-year write-off +113 |
| Fuel cells (SOFC) | 155 | **162** | 104–221 | 30% ITC −30; no stack replacement −21; 5-year write-off +113 |
| On-site CC | 90 | (193) | n/a | Not a realistic islanded design (see caveats) |

Site size matters for turbines:
- System LCOE for turbines is 176 at 100 MW, 150 at 300 MW and 133 at 1,000 MW.
- For engines it is 133, 126 and 122.

Fuel is 34% of engine system cost, 34% of turbine system cost and 20% of SOFC cost. Capital is 50–60% of engine and turbine cost.

**Leased bridge power (`bridge_lease.csv`).** Solaris Energy Infrastructure's Power Solutions segment earned "approximately $158 million" in Q2 2026 on "approximately 950 MW of capacity earning revenue" ([Q2 2026 release](https://ir.solaris-energy.com/~/media/Files/S/Solaris-IR/press-release/sei-q2-2026-earnings-release.pdf)). That is about $56/kW-month, the fleet average including services and ancillary revenue.
- At 80% load factor plus 2027 strip fuel (assuming the customer buys fuel), that is about **$129/MWh** if the leased MW equal peak load.
- It is **$183/MWh** if the lessee also rents N+k spare turbines.
- These are year-1 cash costs, not 20-year levelized values. The $129 sits close to the owned-system engine figure and between the bare and system turbine figures; the $183 is above both.

## Grid comparison (`grid_references.csv`)

| Reference | Observed | Levelized, inflation only | Levelized, energy tracks gas path |
|---|---|---|---|
| PJM wholesale + transmission, 2025 (IMM total price) | 82.7 | 102 | 107 |
| Same, with capacity at the 2026/27 BRA $329.17/MW-day and 80% LF | 86.7 | 107 | 112 |
| ERCOT wholesale all-in, 2025 | 38.7 | 48 | 52 |
| EIA industrial retail, Jan–Aug 2026: TX / US / VA / OH / PA | 68 / 91 / 101 / 102 / 108 | 81 / 109 / 121 / 123 / 130 | n/a |

Sources and adjustments:
- PJM figures are from the [2025 State of the Market](https://www.pjm.com/-/media/DotCom/committees-groups/committees/mc/2026/20260424-special/2025-annual-state-of-the-market-report-for-pjm.pdf), "Total cost of wholesale power": energy $49.28, capacity $13.09, transmission $18.53, total $82.67.
- The PJM capacity price is from the [2026/27 BRA release](https://www.pjm.com/-/media/DotCom/about-pjm/newsroom/2025-releases/20250722-pjm-auction-procures-134311-mw-of-generation-resources-supply-responds-to-price-signal.pdf). The capacity term assumes the site draws at peak during PJM's summer coincident peaks (PLC = average/0.8 = $17.1/MWh). If PLC equals average load, it is $13.7.
- The ERCOT figure is derived: the IMM's 2024 all-in cost "$34 per MWh" ([2024 SoM](https://potomaceconomics.com/wp-content/uploads/2025/06/2024-State-of-the-Market-Report.pdf)), raised by the "13.8%" increase the IMM reports for 2025 ([2025 SoM to TAC](https://www.ercot.com/files/docs/2026/08/06/2026-08-SoM-for-TAC-JDMc.pdf)). It excludes transmission (4CP) and delivery charges, which no large load avoids, so Texas industrial retail is the more realistic bound.
- Retail prices are from EIA Electric Power Monthly Table 5.6.B.
- Observed prices (2025; retail 2026) are carried to the 2027 start at 2.25% a year before levelizing.

Reading:
- **PJM.** At current order prices, off-grid engines (~$126) cost about 12–17% more than delivered PJM wholesale power on a like-for-like levelized basis ($107–112). Turbines (~$150) cost about 33–40% more. These premiums are probably floors. The capacity term was adjusted to a flat 80%-load-factor load, but the energy and transmission terms were left at PJM's load-weighted, peak-allocated system averages, which overstate what a flat load pays per MWh.
- **ERCOT.** Off-grid gas costs 1.5–1.8× the average Texas industrial retail price ($81 levelized) and 2.4–2.9× wholesale all-in.
- **Older orders.** At pre-boom capex (the low column), engines are roughly at parity with PJM.
- **Fuel cells** are above every grid reference unless they get both the ITC and the low capex.

## Caveats

1. **These are owned-asset costs.** Many islanded sites running today use leased or mobile units as bridge power (xAI Memphis, Abilene, VoltaGrid). The Solaris fleet average above is the only lease anchor we found, and it is a fleet revenue average, not a contract rate. The 5- and 10-year write-off rows bound a site that drops its gas once the grid arrives, ignoring resale or redeployment.
2. **Several capex numbers rest on one statement or on judgment.** Engine and turbine central capex rests on a single Brattle statement ("approach or exceed $3,000/kW"), not on a bottom-up study of a data-center plant. That statement is about grid-connected peakers that "leverage existing gas/electric interconnection", and here it is applied to both engines and turbines. The high case borrows a frame-CT escalation for engines. The SOFC low case and the stack-replacement assumption are ours. No primary source gives a Bloom PPA price.
   - **Unverified checks**, seen only in search snippets:
     - RaboResearch (June 2026), ~$107/MWh for engines;
     - Modo's "illustrative" $125/MWh recip price;
     - Black Hills' $1.8B for 564 MW of gas for Google's Cheyenne campus (~$3,200/kW, technology not stated).
3. **The redundancy treatment is simple.** It assumes independent failures, a flat load at peak and no batteries. Real designs share spares with UPS and diesel. Spinning reserve and transient response for AI load swings usually need batteries, which add about +$8 at 0.25 MW per MW of peak (AEO2026 battery cost).
4. **On-site CC "system" costs are not meaningful.** Islanding 250 MW blocks to four nines takes 3× overbuild. In practice nobody builds islanded CC; Cleanview found almost none planned. The CC bare-plant number ($90) is a reference for a grid-tied or hybrid design only.
5. **The grid comparison leaves out real costs on both sides.** It omits interconnection and network-upgrade costs that large loads increasingly pay, and the multi-year wait for grid service. Those are the reason sites go off-grid; the premium buys time to power. The grid's own new-build costs are rising for the same turbine-scarcity reason, and ERCOT's draft CONE doubles to $290/kW-yr. Today's grid prices may therefore understate future ones.
6. **Tax treatment is simplified.**
   - The fuel-cell ITC is 30% under §48E(j) for construction from 2026. Its application to a given project, and the end-2028 placed-in-service timing reported for AEP, are from secondary legal summaries.
   - 100% bonus depreciation (OBBBA) helps only an owner with tax appetite, and is shown as a sensitivity (−5 to −18).
