# Addendum: regional sensitivity (pre-analysis plan R2, frozen 2026-10-24 before any regional result was inspected)

Zeke requested this on 2026-10-24 and made four choices: project-hotspot regions; matched pairing plus a local-gas sensitivity; a heatmap plus basin-range bars; and an addendum with one review.
R1 was reviewed in `reviews/review_regional_v1.md`; the reviewed text is `reviews/PLAN_regional_R1_as_reviewed.md`. R2 adopts every must-fix item and most should-fix items. Exceptions are listed in §9.
`regional.py` ran once as a smoke test before the review. Its outputs were deleted uninspected.

The main analysis (`PLAN.md`, `METHODS.md`) carries over unchanged: emissions function, heat rates, slip, f = 0.093, 1% BTM loss and 3% grid transmission loss, and GWP100 primary.

## 1. Question
Do the main verdicts hold in each region where BTM data centers are being sited, once that region's grid and its supplying basin's leak rate are used? The main verdicts are that recips and turbines are worse than the grid, and that fuel cells and on-site CC tie a new grid NGCC.

## 2. Regions (corrected per review M1, M2)
| Region | Sites (Cleanview) | EIA-930 BA (primary) | eGRID bracket: BA / subregion | Supply basin, low / central / high L |
|---|---|---|---|---|
| West Texas | Stargate Abilene, Frontier (Shackelford) | ERCO | ERCO / ERCT | Permian TX 2.4 / 3.6 / 4.2% |
| Texas Panhandle | Fermi Matador (Amarillo, up to 17 GW), Crusoe Goodnight (Armstrong Co.) | SWPP | SWPP / SPSO | Anadarko 1.4 / 1.7 / 3.6% (high = Permian TX via Waha) |
| El Paso / Santa Teresa NM | Stargate Jupiter, Meta El Paso | EPE | EPE / AZNM | Permian Delaware 1.2 / 2.4 / 3.6% |
| Ohio / PA / WV / VA | Meta and EdgeConneX New Albany, Monarch, Homer City, Sterling | PJM | PJM / RFCW | Appalachia 0.4 / 0.6 / 0.9% |
| Memphis | xAI Colossus 1 and 2 (data halls in Memphis; Colossus 2 turbines at Southaven MS) | TVA | TVA / SRTV | Haynesville 0.4 / 0.7 / 1.0% |
| Cheyenne WY | Crusoe/Tallgrass Project Jade | WACM | WACM / RMPA | Rockies, DJ central: 1.0 / 1.2 / 5.2% (DJ is labelled **the most BTM-favourable defensible basin**; GGR is the high case) |
| Central Utah | Joule (Millard Co.), Delta | PACE | PACE / NWPP | Rockies via Kern River, GGR central: 1.2 / 5.2 / 7.7% (Uinta alone could not supply 4–12 GW) |

The MISO row is dropped. Colossus 2's load is in Memphis/TVA (review M2, Cleanview text). Southaven/SRMV is shown only as a note.

## 3. Grid reference A (review M3, M8)
- **Primary: EIA-930 consumption-based CO2 intensity** for the BA, 2025, from EIA's MRIO allocation of interchange in the per-BA workbooks (`scripts/eia930_intensity.py` → `data/eia930_intensity.json`). One rule applies to every region.
  - Validation: EIA-930 2023 production intensity vs eGRID2023 BA. ERCO +3%, PJM −1%, MISO +3% (pass). Smaller BAs: SWPP +7%, TVA −7%, PACE −5%, WACM −21%, EPE −19%, PNM +80%.
  - The small-BA gaps come from attributing jointly owned and dynamically scheduled units, which is what makes the consumption basis preferable there. This is stated as a caveat.
- **Bracket:** eGRID2023 BA production and eGRID subregion (the §2 table).
- **Grid upstream on consumed MWh.** Gas and coal fuel are derived from consumed CO2 × the BA's generation CO2 share by fuel, divided by 53.06 (gas) and 96 (coal) kg CO2/MMBtu. This assumes imports have the BA's own fuel mix. Terms added:
  - gas supply CO2 (f) and upstream CH4 at the pairing's L;
  - **regional coal-mine CH4** (range in `data/basin_leak_rates.json` cmm_note): surface/PRB/lignite 0.04 (0.02–0.06), underground 0.26. PJM 0.25, TVA 0.15, PACE 0.13, others 0.04;
  - **coal supply-chain CO2** at 2% (1–3%) of coal combustion CO2;
  - all divided by (1 − 0.03).
- EIA-930 is CO2 only. Combustion CH4/N2O (<0.5% of the total) is omitted on the grid side and kept on the BTM side, which works slightly against BTM. The effect is noted.

## 4. Reference B and pairings (review S3)
- **B:** new H-class NGCC (HR 6.2), burning the **local basin's** gas in every pairing. A new grid plant in the region would take the same pipeline supply.
- **Matched (primary):** BTM, grid A gas and B all at the basin L.
- **Local vs national (sensitivity):** BTM and B at the basin L; grid A gas at the national 2.3%, because the existing fleet burns a pipeline mix.
- **Energy-allocation sensitivity:** L × gas share of boe (MacKay 2026 Table 1) on all sides.

## 5. Classification (review M6, M7)
Each region × case gets one of four mutually exclusive states. They are defined with cell-specific tie bands from a per-region MC (§6):
- **Worse:** above A and above B.
- **Between:** above one reference and below or tied with the other. The output names which one.
- **Better:** below both.
- **Tied:** within the band of both.

The pre-registered "worse" verdict from the main analysis (above A AND above B) is unchanged. Where A > B (coal-heavy grids), that test reduces to "above A". The four-state view stops a recip that sits below a coal-heavy 2023 average from being reported simply as "not worse".

**Pre-registered headline wording for "Between" cells** where BTM < A and BTM > B: *"Against the [region] grid's 2023–25 average, which is coal-heavy, gas on site comes out ahead. It still emits X% more than a new gas plant on the grid would. Large new load can also delay coal retirements, which would make connecting to the grid worse than the average implies, and the comparison shifts as coal retires."* X is computed.

## 6. Per-region Monte Carlo (review S1)
N = 20,000 correlated draws per region:
- **L:** triangular(low, central, high), shared across BTM, A and B under matched pairing.
- **CMM factor:** uniform over the region's range.
- **Coal supply-chain f:** U(1%, 3%).
- **Main-analysis draws:** CH4 mass fraction, gas f, GWP CH4, grid loss, BTM heat rate and recip slip, as in the main analysis.

The grid factor is kept out of the MC because it is structural and is handled by the bracket. Each cell's tie band = max(5%, half-width of the 90% interval of the relative gap), computed separately for A and B.

## 7. Outputs
- **Heatmap:** regions × the four primary prime movers, colored by % gap vs A (primary) at matched central L. Each cell shows its four-state label, and a side column gives % vs B.
- **Basin-range bars:** for each region, BTM totals across basin L (low / central / high) for each prime mover, with grid A as a band over the same L range and B as a marker.
- **Tables:** `results/regional/*.csv`, including the GWP20 and eGRID-bracket variants and Cambium 2024 LRMER for each site's GEA region (context, pre-OBBBA).

| Region | Cambium GEA |
|---|---|
| West Texas | ERCOT |
| Texas Panhandle | SPP_South |
| El Paso / S. NM | WestConnect_South |
| PJM | PJM_West |
| Memphis | SERTP |
| Cheyenne | WestConnect_North |
| Central Utah | NorthernGrid_South |

## 8. Predictions (recorded before running)
- **Recips and simple cycle:** "Worse" in West Texas, PJM and Memphis. Probably "Worse" in the Panhandle and El Paso as well, since SWPP and EPE consumption intensities (430, 347) sit below recip CO2 alone (≈492).
- **Cheyenne and Central Utah:** A (consumption basis 604 and 548, plus upstream) may sit near or above recip totals, so recips could be "Between" or "Worse" depending on L. CC and SOFC are likely "Between": below A, tied with or above B.
- **El Paso:** EPE's grid burns about as much gas per MWh as SOFC/CC, so methane can move those cells either way (review M6). No direction is predicted.
- **Leak rate:** at Uinta/GGR rates (5–8%) upstream CH4 adds about 100–250 kg/MWh to BTM at GWP100 (review M6 correction). The basin range will dominate the bars for the Rockies regions.

## 9. Review items not adopted, or adopted partly
- **Post-retirement sensitivity for PACE/WACM** (S4): not built. Cambium LRMER serves as the forward-looking context instead. The "Between" wording already flags retirements.
- **Regional T&D** (S6): the flat 3% is kept, as the reviewer recommended.
- **Plant-level CMM** from EIA-923 coal receipts joined to GHGRP FF (M8 route 2): not built. Region-level mine-type ranges are used instead.
- **Main-analysis latent issues** (flagged, not changed):
  - The national CMM factor overstates ERCOT's grid by about 7 kg/MWh (1.7% of A), which favors BTM.
  - Coal supply-chain CO2 is omitted, by about 3 kg/MWh in ERCOT/PJM, which favors the grid.
  - These partly offset, and neither changes a main verdict. They are recorded in METHODS.
