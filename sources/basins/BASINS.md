# US basin-level oil and gas methane loss rates (compiled 2026-10-24)

Purpose: basin "methane intensity" (CH4 emitted as % of gas production) to pair with data-center regions.

## Verification tags
- VERIFIED-FULLTEXT: I read the full paper/page text; quote is from a local copy in this folder (file named).
- VERIFIED-FULLTEXT (WebFetch-summarized): page read through the WebFetch summarizer only, no local copy; treat quote as paraphrase-grade.
- ABSTRACT-ONLY: only the abstract was read.
- UNVERIFIED: search snippet, news coverage, or memory.
No DOI is listed unless it appeared on a page I opened.

## Definitions that change the number (read first)
| Source family | Numerator | Denominator | Notes |
|---|---|---|---|
| MacKay et al. 2026 (MethaneAIR) | oil+gas sector CH4, entire sector (not just upstream), after subtracting non-O&G | gross natural gas production x CH4 content (Eq. 2) | Basin shares of oil vs gas not removed; oil-basin intensities are inflated relative to a gas-only attribution |
| Varon et al. 2026 (TROPOMI/IMI) | oil+gas CH4 from inversion | "dry gas production" x CH4 content (80% Permian, 90% for the four other basins) | Whole sector |
| Sherwin et al. 2024 (aerial + simulation) | well-site + midstream (gathering, processing, pipelines) | "covered natural gas production" (Enverus, CH4 mass) | Midstream is 19-54% of regional emissions |
| Peischl 2015/2018 (aircraft mass balance) | O&NG CH4 attributed by ethane/CH4 | total natural gas produced/extracted, CH4-content adjusted | Whole sector in region |
| Lin 2021 (tower) | all CH4 in footprint attributed to O&G | natural gas production | Includes oil wells |
| Robertson 2017 | well-pad only (OTM 33a) | gross CH4 produced at pads ("TNMA") | Upstream well pads only, excludes midstream |
| EDF/MethaneSAT, AMI | total basin O&G | gas produced/sold (marketed) | Marketed < gross |
| MiQ | facility | gas sent to sales | upstream |

Energy-allocation caution: all values above allocate 100% of O&G methane to gas. For oil-heavy basins (Permian, Bakken, Eagle Ford) an energy-based split lowers the gas-attributed rate by roughly the oil energy share (see share column).

## Oil vs gas share of output (energy basis)
Source: MacKay et al. 2026 Table 1 (Enverus 2023, Mboe, 1 boe = 169.9 m3 gas) [VERIFIED-FULLTEXT, `acp26_1179_2026.txt`]. These are Enverus gross production in million boe, not EIA marketed gas; EIA basin-level shares not retrieved. Gas share of boe = gas/(oil+gas), my arithmetic; their column "Percent of total from oil/gas" is quoted where different.

| Basin | 2023 oil Mboe | 2023 gas Mboe | Oil%/gas% (paper) |
|---|---|---|---|
| Anadarko | 100 | 342 | 23/77 |
| Appalachian | 63 | 2167 | 3/97 |
| Barnett | 7 | 144 | 4/96 |
| Denver-Julesburg | 170 | 183 | 48/52 |
| Eagle Ford | 432 | 487 | 47/53 |
| Greater Green River | 9 | 147 | 6/94 |
| Haynesville-Bossier | 8 | 983 | 1/99 |
| Permian | 2162 | 1410 | 61/39 |
| Piceance | 5 | 73 | 6/94 |
| Uinta | 52 | 46 | 53/47 |
| Bakken | 442 | 200 | 69/31 |
| Arkoma-Fayetteville | 0.3 | 63 | 1/99 |
| San Juan, Powder River | not in this paper | | gap |

## Primary multi-basin sources (opened)
- MacKay et al. 2026, ACP 26, 1179-1192, DOI on page 10.5194/acp-26-1179-2026. URL opened: https://acp.copernicus.org/articles/26/1179/2026/acp-26-1179-2026.pdf (local `acp26_1179_2026.pdf/.txt`). MethaneAIR, 32 flights, 2023, 12 basins covering 70% of onshore production. Quote: "estimated gross gas normalized methane loss rates ... Haynesville-Bossier 95 400 (± 28 %) 0.9 %" (Table 3). Uncertainties are given only for emissions in Table 3 (emission ± %), not on the loss rate itself. Flights cover only part of some basins (production coverage 44% Greater Green River, 48% Bakken).
- Varon et al. 2026, ES&T 60(1), DOI on page 10.1021/acs.est.5c08745, open access via Europe PMC PMC12810242. URL opened: https://www.ebi.ac.uk/europepmc/webservices/rest/PMC12810242/fullTextXML (local `varon2026_epmc.xml/.txt`). TROPOMI + IMI 25 km, weekly.
- Sherwin et al. 2024 Nature, corrected 29 May 2026, DOI 10.1038/s41586-024-07117-5. URL opened: https://www.nature.com/articles/s41586-024-07117-5 (abstract; paywalled body) and Supplementary Information PDF https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41586-024-07117-5/MediaObjects/41586_2024_7117_MOESM1_ESM.pdf (local `sherwin_SI.pdf/.txt`; its Table S10 reproduces the corrected 2.43% total, so it is the corrected SI). Source-data xlsx saved (`sherwin_MOESM3_srcdata.xlsx`, `sherwin_MOESM4_srcdata.xlsx`; not executed).
- Lu et al. 2023 is PNAS 120, e2217900120 (GOSAT, 2010-2019), NOT ACP. DOI on page 10.1073/pnas.2217900120. URL opened: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10151460/ (local `lu2023_pnas_pmc.txt`). Per-basin values are in a figure not extractable from text; only ranges quoted below. (The ACP URL I guessed returned 404.)
- Shen et al. 2022 ACP 22, 11203 (DOI 10.5194/acp-22-11203-2022), URL opened https://acp.copernicus.org/articles/22/11203/2022/ (local `shen2022.txt`): reports basin emissions in Tg/yr (figures), not loss rates; the text gives only Permian 3.5-4.6%. Basin loss rates for Haynesville etc. from Shen are not in the text. [VERIFIED-FULLTEXT for what is said; per-basin loss rates = gap]
- Peischl 2018 JGR 123, 7725-7740, DOI on page 10.1029/2018JD028622, PDF read from NOAA repository (local `peischl2018_jgr.pdf/.txt`, URL https://repository.library.noaa.gov/view/noaa/21785/noaa_21785_DS1.pdf, obtained through WebFetch tool-result cache).
- Peischl 2015 JGR 120, 2119, DOI on page 10.1002/2014JD022697, URL opened https://www.ourenergypolicy.org/wp-content/uploads/2015/07/jgrd52015.pdf (local `jgrd52015_peischl.pdf/.txt`).

---

## Haynesville (Louisiana / East Texas)  | gas share of boe 99%
| Value | Years | Denominator | Method | Source (URL opened) | Verification |
|---|---|---|---|---|---|
| 0.5 +/- 0.1% (2022-23 mean); 0.6% (2022) to 0.4% (2023); emissions 0.46 +/- 0.11 Tg/yr | 2022-2023 | dry gas production x 90% CH4; whole O&G sector | TROPOMI IMI weekly inversion | Varon 2026, Europe PMC full text. Quote: "Average methane intensity was 2.1 +/- 0.5% in the Anadarko, 2.6 +/- 0.6% in the Barnett, 1.1 +/- 0.2% in the Eagle Ford, and 0.5 +/- 0.1% in the Haynesville." | VERIFIED-FULLTEXT |
| 0.9% (emissions 95,400 kg/h, +/-28%) | 2023 | gross gas x CH4 content; whole O&G sector; 95% of basin production covered, 3 flights | MethaneAIR | MacKay 2026 Table 3 | VERIFIED-FULLTEXT |
| 1.0 +/- 0.5% (Apr 2015); 1.5 +/- 0.5% (Jun 2013 as recomputed) | 2015; 2013 | produced gas, CH4-adjusted; whole O&G | NOAA WP-3D mass balance | Peischl 2018: "1.0 +/- 0.5% in the Haynesville region of Texas and Louisiana"; "decreased from 1.5 +/- 0.5% to 1.0 +/- 0.5%" | VERIFIED-FULLTEXT |
| 1.0-2.1% | 2013 | total gas extracted | aircraft mass balance | Peischl 2015 abstract: "loss rate from production operations of 1.0-2.1% from the Haynesville region" | VERIFIED-FULLTEXT |
| <1.5% (2010-19 mean, Haynesville, Marcellus, Fayetteville) | 2010-2019 | gas produced | GOSAT + GEOS-Chem | Lu 2023 PNAS: "gas-dominated regions such as the Marcellus, Haynesville, and Fayetteville have much lower methane intensity of less than 1.5%" | VERIFIED-FULLTEXT (range only) |
| "about 1%" (Haynesville and Appalachian) | 2023 | | MethaneAIR preprint press quote | WESA story https://www.wesa.fm/environment-energy/2024-09-12/methane-emissions-gas-industry-study: "The loss rates from these two places are about 1%." (Gautam) | secondary news, saved `wesa_nepa.txt`; superseded by MacKay 0.9% |
Varon states these four-basin intensities are "a factor of 2-3 lower than estimated by Lu et al. for the years 2010-2019" (except Barnett).
**Best central and range: 0.7% (range 0.4-1.0%).** Two independent 2022-23 methods (TROPOMI 0.5%, MethaneAIR 0.9%) bracket it; aircraft 2015 (1.0%) is consistent. Note MacKay is gross-gas based and Varon dry-gas based. Sub-1% is robust; the precise value within 0.4-1.0 is not.

## Appalachia (Marcellus + Utica; not separable in sources found)  | gas share 97%
| Value | Years | Denominator | Method | Source | Verification |
|---|---|---|---|---|---|
| 0.52% (95% CI 0.30-0.62%) | 2025 surveys (Mar-Oct 2025) | natural gas production; "full natural gas supply chain" per AMI release (upstream+gathering/midstream within basin; exact boundary not stated) | multi-scale: aerial (Bridger, Insight M, ChampionX) + inventory; ~6,600 sites | EDF blog https://blogs.edf.org/energyexchange/2026/05/28/low-producing-conventional-wells-high-loss-rates-drag-down-appalachias-energy-industry/ (local `edf_appalachia.txt`): "AMI estimates that the region's methane loss rate is 0.52% of natural gas production (95% CI: 0.30-0.62%)". AMI release (https://www.miningstockeducation.com/2026/03/..., local `ami_press.txt`): "a methane loss rate of 0.52% from the full natural gas supply chain" | AMI report itself NOT opened; industry-led (AMI members >50% of production). Two secondary pages agree. Conventional wells 18.3% vs unconventional 0.09% (EDF blog) |
| 0.6% | 2024-2025 | marketed gas | MethaneSAT | EDF blog above quotes it; Inside Climate News (WebFetch only; direct curl 403): "0.6 percent of all marketed gas production in the Appalachian Basin"; "The data have not yet been peer reviewed." | UNVERIFIED primary (no MethaneSAT report opened) |
| 0.9% (emissions 160,000 kg/h +/-47%) | 2023 | gross gas x CH4; whole O&G; 68% of production covered | MethaneAIR | MacKay 2026 Table 3 | VERIFIED-FULLTEXT |
| 0.71% [0.61-0.81%] (PA portion only) | 2021 | covered gas, CH4 mass; well site + midstream | Carbon Mapper aerial (AVIRIS-NG) + simulation | Sherwin SI Table S10 "CM Pennsylvania/2021 73 [63, 83] t/hr; 10,242 t/hr production; 0.71 [0.61, 0.81]" | VERIFIED-FULLTEXT (SI). This is the 0.71% "gas-rich" low end in the abstract |
| 0.36% (2 sigma 0.27-0.45%) inverse; 0.40% (0.08-0.72%) mass balance | May 2015 | total gas production; NE PA unconventional production+gathering | WRF-Chem inversion + aircraft | Barkley 2017 ACP abstract: "0.36 % of total gas production, with a 2sigma confidence interval between 0.27 and 0.45 %" (https://acp.copernicus.org/articles/17/13941/2017/acp-17-13941-2017.pdf, local `barkley2017_acp.pdf`) | VERIFIED (abstract+first page); NE PA only |
| 0.18-0.41% | 2013 | gas extracted | aircraft | Peischl 2015 abstract (NE PA Marcellus) | VERIFIED-FULLTEXT |
| <1.5% | 2010-19 | | GOSAT | Lu 2023 | range only |
**Best central and range: 0.6% (range 0.4-0.9%).** AMI 0.52% and MethaneSAT 0.6% agree, Sherwin PA 0.71% is similar, MethaneAIR 0.9% is the high side (gross denominator, whole-sector, includes coal-region ambiguity); SW PA conventional wells push the basin figure above NE PA's 0.36%. Marcellus (NE PA, ~0.4%) vs Utica/SW PA/WV not separable here.

## Uinta (Utah)  | gas share 47%
| Value | Years | Denominator | Method | Source | Verification |
|---|---|---|---|---|---|
| 7.7% (emissions 34,900 kg/h +/-50%) | 2023 | gross gas x CH4; whole O&G; 92% production covered, 2 flights | MethaneAIR | MacKay 2026 Table 3; text: "Uinta and Piceance had higher loss rates (> 7 %)" | VERIFIED-FULLTEXT |
| 5.55% [5.14-6.02%] | 2020 | covered gas CH4; well site + midstream | Carbon Mapper aerial + simulation | Sherwin SI Table S10 "CM Uinta/2020 19 [18, 21] 351 5.55 [5.14, 6.02]". Press (KUNC) gave "nearly 6%" pre-correction | VERIFIED-FULLTEXT |
| 6-8% (6.3 +/- 0.6% for HRRR meteorology; 6.3 +/- 0.3% slope method) | 2015-2020 | natural gas production; all O&G incl. oil wells | tower inversion (STILT), Horsepool tower | Lin 2021 Sci Rep 11:22291, DOI on page 10.1038/s41598-021-01721-5, https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8595340/ (local `lin2021_uinta_pmc.txt`). Quote: "emissions remained steady over the same years, at ~ 6-8%, among the highest in the U.S." | VERIFIED-FULLTEXT |
| 2.8% (95% CI 1.0-8.6%) | ~2014-15 | gross CH4 produced at pads (TNMA) | OTM 33a well-pad | Robertson 2017 ES&T 51, DOI on page 10.1021/acs.est.7b00571, abstract via Europe PMC API | ABSTRACT-ONLY; well pads only |
| ~9% | early 2024 | marketed | MethaneSAT prelim | search summary only | UNVERIFIED |
| 7.8% | 2023 | not stated | MethaneAIR early release | Deseret News https://www.deseret.com/utah/2024/08/07/methane-pollution-utah-study/ (local `deseret_uinta.txt`): "the Uinta Basin in eastern Utah has the country's highest loss rate of 7.8%" | secondary news; superseded by final 7.7% |
**Best central and range: 6.5% (range 5.5-8%).** Three independent methods (tower, aerial inventory, airborne imaging) converge on 5.5-8%; older pad-level OTM value (2.8%) predates decline in gas production and excludes midstream. Note the basin is 47% oil, so a gas-only energy-allocated rate would be about half.

## Greater Green River / Pinedale-Jonah (Wyoming)  | gas share 94%
| Value | Years | Denominator | Method | Source | Verification |
|---|---|---|---|---|---|
| 5.2% (emissions 41,800 kg/h +/-27%) | 2023 | gross gas x CH4; whole O&G; only 44% of basin production covered, 2 flights | MethaneAIR | MacKay 2026 Table 3; text: "Greater Green River ... 7.9 times higher than EPA" (O&G) | VERIFIED-FULLTEXT |
| 0.18% (95% CI 0.12-0.29%) | ~2014-15 | gross CH4 at pads (TNMA), Upper Green River (Pinedale/Jonah area) | OTM 33a | Robertson 2017 abstract | ABSTRACT-ONLY; well pads only, no midstream, an old (consolidated, multi-well pad) fleet |
**Best central and range: 5% (range 0.2-5.2%; low confidence).** Only one recent top-down value (partial coverage); the 0.18% pad-level number is not comparable (upstream pads only, 2010s). Treat Wyoming gas as unresolved with a plausible 2-5% range if regional distribution is needed.

## Powder River (Wyoming)
No loss rate found in any opened source. MacKay 2026 (12 basins) excludes it; Sherwin excludes it. **Gap.** If a value is needed, proxy with Greater Green River/Uinta bracket as an explicit assumption, not a measurement. Also note much Powder River gas is coalbed methane plus oil-associated gas (UNVERIFIED, memory).

## Denver-Julesburg (Colorado)  | gas share 52%
| Value | Years | Denominator | Method | Source | Verification |
|---|---|---|---|---|---|
| 1.3% (emissions 24,200 kg/h +/-40%) | 2023 | gross gas CH4; whole O&G; 91% covered, 5 flights | MethaneAIR | MacKay 2026 Table 3 | VERIFIED-FULLTEXT |
| 1.04% [0.95-1.14] (summer), 1.10% [0.99-1.25] (fall) | 2021 | covered gas; well site + midstream | Carbon Mapper + simulation | Sherwin SI Table S10 | VERIFIED-FULLTEXT |
| 2.1 +/- 0.9% | Mar 2015 | produced gas, CH4-adjusted | aircraft mass balance | Peischl 2018: "2.1 +/- 0.9% from the Denver Basin region" | VERIFIED-FULLTEXT |
| 4.1 +/- 1.5% (May 2012); 4.0% (2.3-7.7%) (2008) | 2008, 2012 | | aircraft/mobile | quoted within Peischl 2018 | secondary quote inside verified paper |
| 2.1% (1.1-3.9%) | ~2014-15 | pads TNMA | OTM 33a | Robertson 2017 abstract | ABSTRACT-ONLY |
**Best central and range: 1.2% (range 1.0-2.1%).** Two 2021-23 methods agree at 1.0-1.3%; older 2012-15 values are higher and show a declining trend.

## San Juan (NM/CO)
No recent measured loss rate in opened sources. Karion 2013 aircraft value of 2.6% (coalbed) appeared only in a search-result summary of a slide deck: **UNVERIFIED**. Kort 2014 SCIAMACHY: emissions 0.59 Tg/yr, ~1.8x EPA (search summary; UNVERIFIED). Cusworth 2022 PNAS (opened, `cusworth2022_pnas_epmc.txt`, DOI on page 10.1073/pnas.2202338119) did not survey San Juan in its campaigns list (SJV, Uinta, DJ, Permian, Marcellus). **Gap.** Note part of San Juan is in New Mexico where Delaware sub-basin data (MethaneSAT NM 1.2%, Permian-NM below) are a different basin.

## Anadarko (Oklahoma)  | gas share 77%
| Value | Years | Denominator | Method | Source | Verification |
|---|---|---|---|---|---|
| 2.1 +/- 0.5% (2022-23); 2.3% (2022) to 2.0% (2023); emissions 0.76 +/- 0.15 Tg/yr | 2022-23 | dry gas x 90% CH4; whole O&G | TROPOMI IMI | Varon 2026 | VERIFIED-FULLTEXT |
| 1.4% (49,500 kg/h +/-46%) | 2023 | gross gas CH4; 78% covered, 2 flights | MethaneAIR | MacKay 2026 Table 3 | VERIFIED-FULLTEXT |
| Lu 2023 (GOSAT 2010-19) | | | | Varon says intensities here are 2-3x lower than Lu's; Lu value not extracted | range only |
**Best central and range: 1.7% (range 1.4-2.1%).** Two 2022-23 methods; midpoint.

## Eagle Ford (Texas)  | gas share 53%
| Value | Years | Denominator | Method | Source | Verification |
|---|---|---|---|---|---|
| 1.1 +/- 0.2% (2022-23); 1.2% to 1.0%; 0.46 +/- 0.09 Tg/yr | 2022-23 | dry gas x 90%; whole O&G | TROPOMI IMI | Varon 2026 | VERIFIED-FULLTEXT |
| 2.0% (59,600 kg/h +/-36%) | 2023 | gross gas CH4; 73% covered | MethaneAIR | MacKay 2026 | VERIFIED-FULLTEXT |
| 2.0 +/- 0.6% (west), 3.2 +/- 1.1% (east) | Mar-Apr 2015 | produced gas, CH4-adjusted (77+/-10%, 68+/-9%) | aircraft | Peischl 2018 | VERIFIED-FULLTEXT |
**Best central and range: 1.5% (range 1.0-2.0%).** Satellite and aircraft-imaging differ by 2x; basin is 47% oil so gas-only attribution would be lower.

## Barnett (Texas, Fort Worth)  | gas share ~95%
| Value | Years | Denominator | Method | Source | Verification |
|---|---|---|---|---|---|
| 2.6 +/- 0.6% (2.8% to 2.5%); 0.40 +/- 0.10 Tg/yr | 2022-23 | dry gas x 90% | TROPOMI IMI | Varon 2026 (also says Lu GOSAT gives 2.6% for Barnett) | VERIFIED-FULLTEXT |
| 1.6% (21,900 kg/h +/-60%) | 2023 | gross gas CH4; 80% covered, 1 flight | MethaneAIR | MacKay 2026 | VERIFIED-FULLTEXT |
| 1.88% [1.68-2.08%] ("Fort Worth") | 2021 | covered gas; well site + midstream | Kairos aerial + simulation | Sherwin SI Table S10 | VERIFIED-FULLTEXT |
| 1.5 +/- 1.0% | Oct 2013-Mar 2015 | produced gas | aircraft | Peischl 2018 | VERIFIED-FULLTEXT |
**Best central and range: 2.0% (range 1.5-2.6%).** Four methods cluster 1.5-2.6%; Varon's higher value reflects low and declining production per Varon.

## Permian (supersession check; not redone)
- Varon 2026: 5.2 +/- 0.8% (2019) to 3.2 +/- 0.9% (2023); NM 4.5 +/- 1.3 to 2.1 +/- 0.7%; Texas 5.2 +/- 0.7 to 3.6 +/- 1.0% (Varon text) VERIFIED-FULLTEXT; Permian 4.0 +/- 1.1 Tg/yr.
- MacKay 2026 (newer, 2023, MethaneAIR): Permian 2.4% (314,000 kg/h +/-34%), 8 flights, 88% covered. Supersedes older 2018-20 values for 2023 conditions. VERIFIED-FULLTEXT.
- Sherwin SI (corrected): Kairos NM Permian 2018-20: 9.77% [9.19-10.45]; CM Permian 2019: 4.23% [4.03-4.44]; 2020: 2.46%; summer 2021: 2.04%; fall 2021: 1.89%; Delaware subregion 2019 2.48%, Midland 5.96%.
- EDF/MethaneSAT 2024-25: NM 1.2%, TX 3.1% (marketed denominator), VERIFIED page text, not peer reviewed.
- Bridger 2024 3.13%, Chen 2022, Zhang 2020 as in brief (from prior scan; not reopened).
**Best central: 2.4-3.2% (2023-24), range 1.9-4.2%.** Intensity fell through 2019-2023; oil-share 61%, so gas-only attribution would be about 40% of this.

## Other basins in the multi-basin sources (for completeness)
Bakken: MacKay 2.1% (1 flight, 48% coverage); Peischl 2018 5.4 +/- 2.0% (2015); Lu 2010-19 mean 8.8% (declining -2.3%/yr). Piceance: 7.9%. Arkoma-Fayetteville: 3.1% (MacKay), 1.0-2.8% (Peischl 2015, 2013), Robertson FV 0.09% (0.05-0.15%). 12-basin total: 1.6% (MacKay). Permian: Lu 2010-19 mean 6.3% (Lu text). San Joaquin: 4.22-5.61% (Sherwin SI 2016-17), down to 2.37% in fall 2021.

## National (supersession note)
- Sherwin et al. 2024 corrected (29 May 2026): "six-region weighted average is 2.43% (95% CI 2.27%, 2.59%)", range "0.71% ... to 9.77%". Which regions (from SI Table S10, corrected): the six regions used in the Total are CM Permian/2019 (4.23%), San Joaquin/2016 (4.22%), Denver-Julesburg fall 2021 (1.10%), Pennsylvania/2021 (0.71%), Uinta/2020 (5.55%), Fort Worth/2021 (1.88%). The 9.77% and 0.71% in the abstract are the Kairos NM Permian (not in the Total, which uses CM Permian 2019) and Pennsylvania campaigns. The SI caption says the Total uses "the campaign covering the largest number of well sites in each region" and lists CM Permian/2019; the NM Kairos row is an extra campaign. Interpretation of that last point is mine; verify against the Zenodo data (not opened). The main article body is paywalled; Fig. 2 not read.
- MacKay 2026: 1.6% for 12 basins covering 70% of onshore production (2023), EPA GHGI 0.4% for same regions. Alvarez 2018 2.3% (previously known). Lu 2023 PNAS: US 3.7% (2010) to 2.5% (2019), mean 3.1%, assuming 90% CH4 content.

## Gaps
1. Powder River: no measurement-based loss rate found.
2. San Juan: only unverified old values; no 2020s basin-wide intensity.
3. Marcellus vs Utica separate: not available; only NE PA Marcellus (0.36-0.40% 2015, Barkley) and PA total (Sherwin 0.71%).
4. Peischl 2018 and Karion/Kort values for San Juan not opened beyond what is noted.
5. Lu 2023 PNAS per-basin numbers are figure-only; SI Table S4 not opened.
6. Shen 2022 per-basin loss rates not in text.
7. AMI 2025/26 report, MethaneSAT basin reports (Haynesville, Uinta, DJ) not opened; only EDF/AMI press-level text.
8. EIA basin-level oil vs gas shares not retrieved; Enverus-based boe in MacKay used instead. Powder River/San Juan shares absent.
9. Sherwin corrected Fig. 2 and Zenodo not opened; per-region table above is from SI Table S10.
10. Varon 2026 SI (Fig S2 numbers, weekly data) not opened; Haynesville annual values 0.6 then 0.4% are text-quoted.
11. Different denominators (gross vs dry vs marketed vs sales) not harmonized; differences are a few % relative but unquantified here.
12. Basins above are whole-sector (production + gathering/processing/some transmission in-basin); none are upstream-only except Robertson pads. Downstream transmission/distribution not included in any basin value.
