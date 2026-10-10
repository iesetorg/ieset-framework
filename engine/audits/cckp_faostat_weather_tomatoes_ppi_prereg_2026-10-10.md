# Value-blind CCKP weather to FAOSTAT tomatoes PPI preregistration

Two directional, correlated tests are fixed before opening selected PPI values, flags, null masks, climate measurements, or fitted results. This is descriptive calibration only.

## Selection by identifiers alone

The official FAOSTAT annual single-item producer price index uses element 5539, annual month code 7021, and base 2014–2016=100. Eligible named crop items have a CPC code starting 01; FAO F-code aggregates and labels containing other, n.e.c., total, or primary are excluded. For each candidate, count countries and exposure years t=1992–2024 with exact country item-index keys at t-1, t, t+1 and CCKP tas/pr keys at t plus every 1961–1990 baseline year. Convert FAO M49 to current ISO3 with pycountry; exclude noncountries and KSV. Require at least 1,300 triple-year keys and 55 countries. Select most keys, breaking ties by ascending item code. No measured values, flags, or missingness are used. The selected named item is **Tomatoes**, FAO 388, CPC 01234, with **4299 keys across 143 countries**.

| Rank | Named item | Code | CPC | Key years | Countries |
| ---: | --- | ---: | --- | ---: | ---: |
| 1 | Tomatoes | 388 | 01234 | 4299 | 143 |
| 2 | Maize (corn) | 56 | 0112 | 4296 | 141 |
| 3 | Potatoes | 116 | 01510 | 4009 | 134 |
| 4 | Cabbages | 358 | 01212 | 3849 | 128 |
| 5 | Onions and shallots, dry (excluding dehydrated) | 403 | 01253.02 | 3685 | 122 |
| 6 | Cucumbers and gherkins | 397 | 01232 | 3591 | 119 |
| 7 | Carrots and turnips | 426 | 01251 | 3340 | 111 |
| 8 | Beans, dry | 176 | 01701 | 3310 | 111 |
| 9 | Chillies and peppers, green (Capsicum spp. and Pimenta spp.) | 401 | 01231 | 3309 | 110 |
| 10 | Wheat | 15 | 0111 | 3306 | 108 |

Frozen key roster: `data/pinned_evidence/cckp_faostat_weather_tomatoes_ppi_2026_key_roster.csv`, SHA-256 `7eb0d1745ce5bef394e34dc388a81fbfdf6413c25911b87b042139108bed02f3`. Keys are potential observations, not complete cases.

## Sources and analysis fixed before values

World Bank CCKP observed CRU TS4.10 annual country tas (°C) and pr (mm), raw `data/vintages/world_bank_cckp/cru_ts4_10_tas_pr_annual_global@2026-10-10T141853Z.json`, SHA-256 `b3477a2f1186990e3cdf156e9dd5788573e25ab5381db6ee6cb08e90fe225a14`, previously acquired under `data/manifests/source_lock_cckp_cru_ts410_2026-10-10.yaml`. FAOSTAT annual producer-price panel `data/vintages/faostat/faostat_prices_main@2026-05-02T212150Z.parquet`, SHA-256 `c59917daee0645066ee5730cf24b9d8058900c81d8510f3892cb7819d1e5a05c`; source archive `data/vintages/faostat/prices@2026-05-02T212150Z.zip`, SHA-256 `0eaff92014d4af5fc2f477dbd436a792bfed1a408645e9ed18d8e45ab14fdc6b`. The parquet is a locally derived cache without a tracked archive-to-parquet transform. Matching ignored source files are needed for replay. The selected archive rows will be compared with the parquet after lock, including values and flags. The index Unit field in this local parquet is blank; element and official codebook define the 2014–2016=100 index.

At exposure year t, temperature is absolute annual mean departure from the country's 1961–1990 mean, °C. Precipitation is absolute annual departure from its 1961–1990 mean divided by its baseline sample SD. Both climate variables at t and all 30 baseline years must be finite; baseline precipitation SD must be positive. The response is **log(PPI(t+1)/PPI(t))**; prior PPI growth log(PPI(t)/PPI(t-1)) and the other weather departure are controls. Require exact positive finite PPI values at t-1,t,t+1, index element/month, and flags A, E or X at all three years; exclude I, B, M, blanks, and unknown flags. Disclose admitted flags. Exclude absolute prior or future log growth above 1.0 and countries with fewer than five complete exposure years. No interpolation, nearest-year join, substitute index, source refresh, alternate item, or estimator.

For each of two exposures, fit OLS with country and exposure-year fixed effects, prior PPI growth and the other weather exposure. Use country-cluster CR1 SE and two-sided Student t(G−1). Require at least 500 complete years and 30 countries; at least 100 years and 20 countries with focal absolute departure ≥1 °C or ≥1 baseline precipitation SD; full rank; positive finite country-cluster SE; and no country contributing over 20% of focal exposure sum of squares after residualizing all nuisance terms. Any failed gate is INCONCLUSIVE. The directional hypothesis is **positive** subsequent nominal farm-gate PPI growth after unusually large annual weather departures. A coefficient ≥+0.02 and p≤0.01/2=0.005 is SUPPORTED; ≤−0.02 at the same cutoff is REFUTED; every other estimable result is PARTIAL. Both registered cells remain in the denominator even on failure. No alternative sign, test, item, years, flags, or thresholds may be substituted after opening values.

National annual climate averages do not isolate tomato growing zones or seasons. Local-currency nominal producer prices reflect inflation, currency, market policy, imports, demand, and reporting; these effects can confound country/year FE. FAO data may be estimated or imputed upstream despite the selected row flags. The two exposures share observations and are not independent replications. The 0.01/2 correction does not adjust the wider IESET research search. Zero causal, policy, school, position, or featured credit.

Official source documentation: World Bank CCKP https://climateknowledgeportal.worldbank.org/download-data ; CRU methods https://worldbank.github.io/climateknowledgeportal/docs/collections/cru-x0.5.html ; FAOSTAT agricultural producer prices https://data.fao.org/catalog/dataset/47c17894-8ca1-4bd0-ba4d-6078e919e9b1 ; FAO methodology https://files-faostat.fao.org/production/PP/PP_e.pdf . FAO/World Bank source rights and attribution apply.
