# Value-blind CCKP weather and FAOSTAT crop preregistration

Fifty-six complete, claim-matched cells were fixed before selected climate or crop measurements, flags, null masks, variance, or fits were inspected. Four broad FAO crop groups and ten named crops span staples and agricultural cash crops; two distinct supply margins and two weather departures are tested. Group and named-crop cells overlap and must never be reported as independent replications.

Key roster: `data/pinned_evidence/cckp_faostat_weather_crop_2026_key_roster.csv`; SHA-256 `0df474914d96a59e7fe16d53c33210cc9a46be63b0f56c661efa864a5cbeb5dc`. These are source keys, not measured complete cases.

| Crop item | FAO item code | Margin | Country-years | Countries |
| --- | ---: | --- | ---: | ---: |
| cereals | 1717 | yield | 10131 | 185 |
| cereals | 1717 | area | 10222 | 185 |
| roots | 1720 | yield | 11064 | 198 |
| roots | 1720 | area | 11108 | 198 |
| pulses | 1726 | yield | 9548 | 176 |
| pulses | 1726 | area | 9657 | 176 |
| oilcrops | 1732 | yield | 10245 | 193 |
| oilcrops | 1732 | area | 10394 | 193 |
| wheat | 15 | yield | 6595 | 125 |
| wheat | 15 | area | 6782 | 125 |
| rice | 27 | yield | 6877 | 124 |
| rice | 27 | area | 7246 | 142 |
| maize | 56 | yield | 9071 | 170 |
| maize | 56 | area | 9274 | 174 |
| potatoes | 116 | yield | 8372 | 159 |
| potatoes | 116 | area | 8740 | 160 |
| cassava | 125 | yield | 5940 | 102 |
| cassava | 125 | area | 6058 | 102 |
| soybean | 236 | yield | 4600 | 108 |
| soybean | 236 | area | 5716 | 118 |
| sugarcane | 156 | yield | 5948 | 112 |
| sugarcane | 156 | area | 6453 | 112 |
| coffee | 656 | yield | 4734 | 83 |
| coffee | 656 | area | 5017 | 83 |
| cotton | 328 | yield | 5233 | 100 |
| cotton | 328 | area | 5820 | 100 |
| tomatoes | 388 | yield | 8829 | 174 |
| tomatoes | 388 | area | 9239 | 174 |

## Frozen source custody

World Bank CCKP observed CRU TS4.10 annual country series (tas °C and accumulated pr mm), 1901–2025; exact raw source `data/vintages/world_bank_cckp/cru_ts4_10_tas_pr_annual_global@2026-10-10T141853Z.json`, SHA-256 `b3477a2f1186990e3cdf156e9dd5788573e25ab5381db6ee6cb08e90fe225a14`. Source acquisition manifest: `data/manifests/source_lock_cckp_cru_ts410_2026-10-10.yaml`. FAOSTAT crop panel `data/vintages/faostat/faostat_prod_All_Data_(Normalized)@2026-05-02T212007Z.parquet`, SHA-256 `02d93061467ca6e9a6cc738ba72702271d26abbaa21480c51d04d29b1017734a`; source ZIP `data/vintages/faostat/Production_Crops_Livestock_E_All_Data_(Normalized)@2026-05-02T211649Z.zip`, SHA-256 `c5835418c18f9322e7decbd6800f93a216eaae3cdfa31acb08f0518c0c6d6853`; flag legend `data/vintages/faostat/faostat_prod_Flags@2026-05-02T212007Z.parquet`, SHA-256 `c9c44507c716b6fe7bd22d68febe1752c3cb4d08c11d62e2311092a8bacc2a6d`. FAO parquet is an earlier locally derived cache without a tracked archive-to-parquet transformation; this limits provenance. Matching ignored raw files are required for replay.

FAO crop elements 5312 (harvested area, ha) and 5412 (yield, kg/ha); only A (official), E (estimated) and X (external) flags are admissible. I (imputed), B (break), M (missing), blank and unknown are excluded. Current ISO3 only; geopolitical/historical labels and KSV are not joined.

## Frozen analysis and failure gates

Outcome year t=1963–2024. Crop response is log(value_t/value_(t-1)); prior crop growth t-2→t-1 is controlled. Temperature exposure is absolute annual mean-temperature departure from the country's 1961–1990 mean in °C. Precipitation exposure is absolute departure from the 1961–1990 mean divided by its sample SD. The other departure is controlled in each cell. Annual CCKP labels `YYYY-07` identify annual observations, not July-only values. Require finite positive crop values, finite weather, exact units, FAO A/E/X flags, at least five complete years per country, and absolute current/prior crop log growth no more than 1.0. No interpolation or proxy.

OLS includes country and outcome-year fixed effects, prior crop growth and the other climate departure. CR1 country-cluster standard errors use two-sided Student t(G-1). Each cell needs at least 500 complete country-years in at least 30 countries, at least 100 material-exposure years in at least 20 countries (temperature departure ≥1 °C or precipitation departure ≥1 baseline SD), a full-rank design, positive finite SE, and no country holding over 20% of exposure sum of squares after residualizing all nuisance terms. Failure is INCONCLUSIVE. Negative beta ≤−0.02 with p≤0.01/56 is SUPPORTED; positive beta ≥+0.02 at the same cutoff is REFUTED; all other estimable outcomes are PARTIAL. All 56 remain in the family denominator. The 0.01/56 cutoff does not adjust wider IESET research selection.

These are descriptive country-level associations, not crop-zone weather exposure or causal climate effects. Zero causal, policy, school, position and featured credit. Source rights and attribution apply.

## Official source documentation

- World Bank CCKP selector: https://climateknowledgeportal.worldbank.org/download-data
- World Bank CRU collection and methods: https://worldbank.github.io/climateknowledgeportal/docs/collections/cru-x0.5.html
- FAO crop production catalog: https://data.fao.org/catalog/iso/d24a448b-3b62-4c09-8c1d-4a39bb599876
- FAO database terms: https://www.fao.org/contact-us/terms/db-terms-of-use/en
