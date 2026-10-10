# Value-blind CCKP annual weather to named-crop FAOSTAT PPI preregistration

This registration **supersedes the narrower two-cell registration in commit `278af727f3004e271b87df6d920cdb8a8fea2e11` before any new source-lock commit, selected price/climate measurement or flag access, or model fit**. The earlier registration kept only the top-coverage item rather than the complete eligible family. Its files are removed in the superseding commit; its first-addition history remains visible. The 59-item, 118-cell family below is the sole executable registration.

## Key-only item selection

Use annual FAOSTAT producer price index element 5539, annual month 7021, country M49 mapped to current ISO3 by pycountry, and exact years t−1,t,t+1 for t=1995–2022. Require CCKP tas and pr keys at t and all 1961–1990 baseline years; omit KSV. Named crops have CPC code prefix 01. Exclude F-code aggregates and labels containing other, n.e.c., total or primary. Include nonfood crop products such as cotton lint and unmanufactured tobacco because they satisfy the same CPC rule; do not hand-pick crop types. Require at least 1,300 country-year triples and 55 countries per item. **Every** qualified item is registered with two weather exposures. Only identifiers, labels, codebook, schema and source hashes were read; no Value/Flag columns, null masks or climate measurements were inspected.

Frozen key roster `data/pinned_evidence/cckp_faostat_weather_named_crop_ppi_2026_key_roster.csv`, SHA-256 `1653dab95b99fdd7f409811619b135af4622c90c731a72207b6c59025a167610`: **129,232 item-country-year keys, 59 named items, 118 tests**. Potential keys are not complete measured cases.

| FAO item code | Named item | CPC | Key years | Countries |
| ---: | --- | --- | ---: | ---: |
| 15 | Wheat | 0111 | 2860 | 108 |
| 27 | Rice | 0113 | 2533 | 96 |
| 44 | Barley | 0115 | 2457 | 92 |
| 56 | Maize (corn) | 0112 | 3705 | 141 |
| 71 | Rye | 0116 | 1587 | 58 |
| 75 | Oats | 0117 | 1944 | 73 |
| 79 | Millet | 0118 | 1815 | 70 |
| 83 | Sorghum | 0114 | 2346 | 89 |
| 116 | Potatoes | 01510 | 3465 | 134 |
| 122 | Sweet potatoes | 01530 | 2241 | 90 |
| 125 | Cassava, fresh | 01520.01 | 1847 | 74 |
| 156 | Sugar cane | 01802 | 1828 | 68 |
| 157 | Sugar beet | 01801 | 1567 | 58 |
| 176 | Beans, dry | 01701 | 2863 | 111 |
| 187 | Peas, dry | 01705 | 2277 | 84 |
| 236 | Soya beans | 0141 | 2261 | 85 |
| 242 | Groundnuts, excluding shelled | 0142 | 2359 | 88 |
| 249 | Coconuts, in shell | 01460 | 1496 | 59 |
| 267 | Sunflower seed | 01445 | 1746 | 66 |
| 270 | Rape or colza seed | 01443 | 1542 | 57 |
| 289 | Sesame seed | 01444 | 1552 | 58 |
| 328 | Seed cotton, unginned | 01921.01 | 1831 | 68 |
| 329 | Cotton seed | 0143 | 1809 | 67 |
| 358 | Cabbages | 01212 | 3335 | 128 |
| 372 | Lettuce and chicory | 01214 | 2335 | 89 |
| 373 | Spinach | 01215 | 1502 | 56 |
| 388 | Tomatoes | 01234 | 3714 | 143 |
| 393 | Cauliflowers and broccoli | 01213 | 2288 | 86 |
| 394 | Pumpkins, squash and gourds | 01235 | 2477 | 97 |
| 397 | Cucumbers and gherkins | 01232 | 3111 | 119 |
| 399 | Eggplants (aubergines) | 01233 | 2074 | 81 |
| 401 | Chillies and peppers, green (Capsicum spp. and Pimenta spp.) | 01231 | 2847 | 110 |
| 402 | Onions and shallots, green | 01253.01 | 1490 | 56 |
| 403 | Onions and shallots, dry (excluding dehydrated) | 01253.02 | 3188 | 122 |
| 406 | Green garlic | 01252 | 2280 | 87 |
| 417 | Peas, green | 01242 | 2039 | 76 |
| 426 | Carrots and turnips | 01251 | 2893 | 111 |
| 449 | Mushrooms and truffles | 01270 | 1742 | 65 |
| 486 | Bananas | 01312 | 2340 | 92 |
| 490 | Oranges | 01323 | 2561 | 101 |
| 495 | Tangerines, mandarins, clementines | 01324 | 1601 | 60 |
| 497 | Lemons and limes | 01322 | 2157 | 86 |
| 507 | Pomelos and grapefruits | 01321 | 1673 | 62 |
| 515 | Apples | 01341 | 2307 | 86 |
| 521 | Pears | 01342.01 | 2126 | 79 |
| 526 | Apricots | 01343 | 1715 | 63 |
| 531 | Cherries | 01344.02 | 1793 | 66 |
| 534 | Peaches and nectarines | 01345 | 1924 | 72 |
| 536 | Plums and sloes | 01346 | 2215 | 83 |
| 544 | Strawberries | 01354 | 1952 | 72 |
| 560 | Grapes | 01330 | 2159 | 80 |
| 567 | Watermelons | 01221 | 2467 | 95 |
| 571 | Mangoes, guavas and mangosteens | 01316 | 1994 | 81 |
| 572 | Avocados | 01311 | 1444 | 56 |
| 574 | Pineapples | 01318 | 1824 | 72 |
| 600 | Papayas | 01317 | 1576 | 62 |
| 656 | Coffee, green | 01610 | 1461 | 55 |
| 767 | Cotton lint, ginned | 01921.02 | 1845 | 67 |
| 826 | Unmanufactured tobacco | 01970 | 2852 | 105 |

## Source and analysis contract

World Bank CCKP CRU TS4.10 annual country tas (°C) and pr (mm): `data/vintages/world_bank_cckp/cru_ts4_10_tas_pr_annual_global@2026-10-10T141853Z.json`, SHA-256 `b3477a2f1186990e3cdf156e9dd5788573e25ab5381db6ee6cb08e90fe225a14`, acquisition manifest `data/manifests/source_lock_cckp_cru_ts410_2026-10-10.yaml`. FAOSTAT agricultural producer-price parquet: `data/vintages/faostat/faostat_prices_main@2026-05-02T212150Z.parquet`, SHA-256 `c59917daee0645066ee5730cf24b9d8058900c81d8510f3892cb7819d1e5a05c`; raw ZIP: `data/vintages/faostat/prices@2026-05-02T212150Z.zip`, SHA-256 `0eaff92014d4af5fc2f477dbd436a792bfed1a408645e9ed18d8e45ab14fdc6b`. The parquet is a locally derived cache without a tracked archive-to-parquet transform; selected archive rows will be compared to the cache after lock. The PPI uses base 2014–2016=100 under the official FAO codebook. The local PPI Unit field is blank, so element/month codes and official metadata define the measure. Matching ignored local source files are required for replay.

Temperature exposure at t is absolute annual country mean departure from its 1961–1990 mean in °C. Precipitation exposure is absolute annual country departure from its 1961–1990 mean divided by baseline sample SD. Require both variables finite at t and every baseline year, with positive pr SD. Outcome is subsequent `log(PPI_(t+1)/PPI_t)`; control prior `log(PPI_t/PPI_(t-1))` and the other departure. All three annual single-item PPI values must be finite and positive with row flags A, E or X; I, B, M, blank and unknown flags fail. Disclose admitted flag counts. Exclude absolute prior or subsequent PPI log growth >1.0 and countries with fewer than five complete exposure years. No interpolation, index substitution, source refresh or alternate model.

Each cell uses country and exposure-year fixed effects, prior PPI growth, and the other weather departure in OLS; country-cluster CR1 SE and two-sided Student t(G−1). Gates: at least 500 complete rows and 30 countries; ≥100 material-exposure rows in ≥20 countries (focal departure ≥1 °C or ≥1 baseline pr SD); full-rank design; positive finite SE; and top country ≤20% of focal exposure sum of squares residualized on all nuisance terms. Failed gate = INCONCLUSIVE. Directional prediction: unusually large weather departure is associated with higher subsequent nominal PPI growth. SUPPORTED iff beta ≥+0.02 and two-sided p≤0.01/118=8.47457627119e-05; REFUTED iff beta ≤−0.02 at the same p cutoff; otherwise PARTIAL when estimable. All 118 cells, including failures, remain in one Bonferroni denominator. No post-value tuning.

Annual national weather misses crop zones and seasons. Nominal local-currency farm-gate indices respond to inflation, exchange rates, imports, demand, policy, storage and reporting. FAO may estimate source data upstream. The correlated item/exposure cells are not independent replications; this correction does not adjust wider IESET research selection. This is **descriptive calibration only** with zero causal, policy, position, school or featured credit.

Official documentation: FAOSTAT agricultural producer prices https://data.fao.org/catalog/dataset/47c17894-8ca1-4bd0-ba4d-6078e919e9b1 ; FAO PPI methodology https://files-faostat.fao.org/production/PP/PP_e.pdf ; World Bank CCKP https://climateknowledgeportal.worldbank.org/download-data ; CRU methods https://worldbank.github.io/climateknowledgeportal/docs/collections/cru-x0.5.html . FAO/World Bank source rights and attribution apply.
