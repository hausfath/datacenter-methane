# Addendum: regional sensitivity (pre-analysis plan, draft R1)

Requested by Zeke on 2026-10-24, after the main analysis. These choices are his:
- regions are the hotspots where Cleanview's BTM projects are sited;
- supply pairing is matched, with a local-gas sensitivity;
- outputs are a heatmap and basin-range bars;
- the process is this addendum plus one combined reviewer.

Everything in `PLAN.md` carries over unless this file says otherwise: the emissions function, heat rates, slip, f, the 1% BTM and 3% transmission losses, GWP100 as primary, and the two-condition test. The main analysis
results do not change.

## 1. Question
The main analysis showed recips and turbines are worse than the grid in ERCOT, PJM and the US. Fuel cells and on-site CC tie a new grid NGCC. This addendum asks whether those verdicts hold in every region where BTM data centers are actually being built,
once each region's own grid mix and the leak rate of its supplying basin are used. The Mountain West (coal-heavy grids) is the obvious place for them to flip.

## 2. Regions, grid factors and basin pairings (eGRID2023 rev2)
| Region | Projects (Cleanview) | Grid, primary | Grid, alternative | Supply basin (matched) |
|---|---|---|---|---|
| West Texas | Stargate Abilene, Frontier, Crusoe Goodnight | ERCO BA (334 kg CO2e/MWh) | ERCT subregion (334) | Permian, Texas side |
| Southern New Mexico / El Paso | Stargate Jupiter, Meta El Paso | AZNM subregion (320) | EPE BA (459), PNM BA (179) | Permian, New Mexico side (Delaware) |
| Ohio / PA / WV / VA / NJ | Meta and EdgeConneX New Albany, Monarch, Homer City, Vineland, Sterling | PJM BA (326) | RFCW (416), RFCE (272) | Appalachia (Marcellus/Utica) |
| Memphis / N. Mississippi | xAI Colossus 1 (TVA), Colossus 2 Southaven (MISO / Entergy MS) | TVA BA (292); MISO BA (448) for Southaven | SRTV (410), SRMV (336) | Haynesville / Gulf Coast |
| Wyoming | Crusoe Project Jade (Cheyenne) | WACM BA (854) | RMPA subregion (473) | Green River / Powder River / DJ (from BASINS.md) |
| Utah | Joule (Millard County), Delta Gigasite | PACE BA (644) | NWPP subregion (288) | Uinta (from BASINS.md) |

**Grid-factor rule (for review).** Large ISO/RTO and TVA BAs use their own BA rate, where production and consumption are close. Small or net-exporting BAs (EPE, PNM, PACE, WACM) have
production-based rates that can differ a lot from what local load consumes, because coal-heavy WACM and PACE export power. For these, both the BA and the eGRID subregion are reported. The
**primary is the subregion for NM/El Paso. For Wyoming and Utah, the primary is the BA, with the subregion as the low-side sensitivity.** In the Mountain West the subregion is the choice that favors the grid, while the BA is
conservative toward BTM. Reviewer: is this asymmetric rule defensible, or should the BA be primary everywhere, or the subregion everywhere?

## 3. Leak rates per basin
Central, low and high values per basin come from `sources/basins/BASINS.md` and are fixed in §6 before any regional run. The definitions are those in METHODS (CH4 emitted per CH4 in production,
whole chain), with no oil/gas allocation. An energy-allocated value is a labelled sensitivity for oil-weighted basins (Permian, DJ, Uinta if oil-weighted).

## 4. Supply pairing
- **Matched (primary):** BTM and grid gas both at the basin's central L.
- **Local vs national (sensitivity):** BTM at the basin's L (central, low and high), grid gas at the national 2.3%. This shows where siting next to a leaky or a clean basin matters.

## 5. Outputs and decision rule
- For each region × prime mover (recip, simple cycle, SOFC, on-site CC; rich-burn as secondary): kg CO2e/MWh, % gap vs grid A (primary grid factor) and vs B (new NGCC), verdicts under
  the two-condition test, and the CO2-only state.
- **Tie band.** Reuse the main analysis's MC-widened band per prime mover. Each prime mover gets the largest band it had across the three main regions vs A, because the band is driven mostly by heat rate, f, GWP and
  loss, not region. This avoids re-running the MC 6 × 5 times. Reviewer: acceptable?
- **Heatmap:** regions (rows) × prime movers (columns), colored by % gap vs the primary regional grid at matched central L. A diverging palette centered at 0, cells marked tied / above / below, and the CO2-only
  verdict noted.
- **Basin-range bars:** per region, the BTM total for each prime mover across the basin's low–high L (matched), with the regional grid A as a band that moves with L, plus grid B.
- **GWP20** as a secondary heatmap or annotation.

## 6. Parameters fixed before running
Fixed 2026-10-24 from `sources/basins/BASINS.md`, before any regional run; stored in `data/basin_leak_rates.json`.

| Basin | Low / central / high L | Gas share of boe (MacKay 2026 Table 1) | Sources |
|---|---|---|---|
| Permian (Texas) | 2.4 / 3.6 / 4.2% | 0.39 | central: Bridger LiDAR 2024 TX 3.6% (ES&T 2026) = Varon et al. 2026 TROPOMI TX 3.6% (2023); low: MacKay et al. 2026 basin-wide 2.4% (2023); high: Sherwin SI Permian 2019 campaign 4.23% / Varon 2023 upper ~4.1 |
| Permian (New Mexico / Delaware) | 1.2 / 2.1 / 4.5% | 0.39 | central: Bridger 2024 NM 2.1% = Varon 2026 NM 2.1% (2023); low: MethaneSAT 2024-25 via EDF 1.2% (not peer reviewed); high: Varon NM 2019 4.5% |
| Appalachia (Marcellus/Utica) | 0.4 / 0.6 / 0.9% | 0.97 | central 0.6%: AMI 2026 0.52% (via EDF/AMI release), MethaneSAT 0.6%, Sherwin PA 0.71%; high: MacKay 2026 0.9%; low 0.4% (AMI CI, Barkley 2017 NE PA 0.36%) |
| Haynesville | 0.4 / 0.7 / 1.0% | 0.99 | Varon 2026 0.5±0.1% (2022-23); MacKay 2026 0.9% (2023); Peischl 2018 1.0±0.5% |
| Denver-Julesburg (high: Greater Green River) | 1.0 / 1.2 / 5.2% | 0.52 | central: Sherwin SI DJ 1.10% (2021), MacKay 1.3%; low 1.0%; high: MacKay Greater Green River 5.2% (44% coverage, low confidence) as the Wyoming-supply upper case |
| Uinta | 5.5 / 6.5 / 8.0% | 0.47 | Lin et al. 2021 6-8% (2015-20); Sherwin SI 5.55% (2020); MacKay 2026 7.7% (2023) |

Region pairing (final):

| Region | Primary grid | Alternatives | Basin |
|---|---|---|---|
| West Texas | ERCOT | sub_ERCT | Permian (Texas) |
| NM / El Paso | sub_AZNM | ba_EPE, ba_PNM | Permian (New Mexico / Delaware) |
| PJM | PJM | sub_RFCW, sub_RFCE | Appalachia (Marcellus/Utica) |
| Memphis (TVA) | ba_TVA | sub_SRTV | Haynesville |
| N. Mississippi (MISO) | ba_MISO | sub_SRMV | Haynesville |
| Wyoming | ba_WACM | sub_RMPA | Denver-Julesburg (high: Greater Green River) |
| Utah | ba_PACE | sub_NWPP | Uinta |

Judgment calls for review:
- Cheyenne sits on the northern edge of the DJ basin, so DJ is the central basin, with Greater Green River (5.2%, low confidence) as the high case.
- The Utah sites (Millard County) are assumed to take Uinta gas. They could also take Wyoming gas via Kern River, which makes Uinta the conservative choice toward the grid.
- The Memphis and Southaven sites take Haynesville gas.
- Denominators are not harmonized across studies (MacKay gross, Varon dry, Sherwin covered, AMI marketed). That changes values by a few percent, relative.
- Energy-allocation sensitivity: L × gas share of boe.

## 7. Predictions recorded before running
- Recips and turbines stay worse than grid A and B in Texas, NM/El Paso, PJM and Memphis.
- In Wyoming and Utah, against the coal-heavy BA averages, every BTM option including recips may come out **below** grid A. They remain above or tied with B, so the two-condition verdict is
  still "not worse", and in those regions the binding comparison becomes B.
- Basin leak rates change totals by tens of kg/MWh. For efficient options this can matter relative to B only through the local-vs-national asymmetry.

Note: `regional.py` was executed once as a smoke test (2026-10-24) before review. Its outputs were deleted uninspected.
