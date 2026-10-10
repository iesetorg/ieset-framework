# Blind FAOSTAT crop supply-response preregistration

Eight complete, claim-matched cells are fixed before any selected price/crop measurements, flags, null masks, sample variance or fits were opened. Only source schemas/codebooks, hashes and item/country/year keys were inspected. The four groups are FAOSTAT's cereals, roots and tubers, pulses, and oilcrops; the two supply margins are harvested area and yield. This is one coherent, correlated family, not eight independent replications.

Key-roster path: `data/pinned_evidence/faostat_relative_price_crop_supply_2026_key_roster.csv`; SHA-256 `8cc8933d4c40092016b25358c25609311681b1eab589c4d77ece1cc6979a0b18`. Source-key counts, which do not establish measured complete cases:

| Cell | Key rows | Countries |
| --- | ---: | ---: |
| `cereals_area` | 4464 | 152 |
| `cereals_yield` | 4457 | 152 |
| `roots_area` | 4646 | 161 |
| `roots_yield` | 4646 | 161 |
| `pulses_area` | 4190 | 142 |
| `pulses_yield` | 4169 | 142 |
| `oilcrops_area` | 4237 | 151 |
| `oilcrops_yield` | 4232 | 151 |

## Source custody

The following ignored local FAOSTAT raw archive/derived-parquet files are pinned by exact SHA-256. They are not copied into Git; replay requires the matching local raw cache. There is no tracked fetch manifest proving the archive-to-parquet derivation, so provenance is limited. The official FAOSTAT database terms and crop/price metadata are cited below.

| Role | Relative source path | SHA-256 |
| --- | --- | --- |
| price_archive | `data/vintages/faostat/prices@2026-05-02T212150Z.zip` | `0eaff92014d4af5fc2f477dbd436a792bfed1a408645e9ed18d8e45ab14fdc6b` |
| price_panel | `data/vintages/faostat/faostat_prices_main@2026-05-02T212150Z.parquet` | `c59917daee0645066ee5730cf24b9d8058900c81d8510f3892cb7819d1e5a05c` |
| crop_archive | `data/vintages/faostat/Production_Crops_Livestock_E_All_Data_(Normalized)@2026-05-02T211649Z.zip` | `c5835418c18f9322e7decbd6800f93a216eaae3cdfa31acb08f0518c0c6d6853` |
| crop_panel | `data/vintages/faostat/faostat_prod_All_Data_(Normalized)@2026-05-02T212007Z.parquet` | `02d93061467ca6e9a6cc738ba72702271d26abbaa21480c51d04d29b1017734a` |
| crop_flag_legend | `data/vintages/faostat/faostat_prod_Flags@2026-05-02T212007Z.parquet` | `c9c44507c716b6fe7bd22d68febe1752c3cb4d08c11d62e2311092a8bacc2a6d` |

FAOSTAT price element 5539 is the annual (month code 7021) 2014–2016=100 producer price index. The crop outcomes are element 5312 area harvested (ha) and element 5412 yield (kg/ha). M49 keys are mapped to current ISO3 and noncountry aggregates excluded. Flags A (official), E (estimated) and X (external organization) are admitted; I (receiving-agency imputed), B (time-series break), M (missing) and blanks are excluded. All admitted flag counts are reported after source lock.

## Frozen analysis and failure gates

For each group and country-year t=1992..2023, x is the annual log change in that group's producer-price index divided by the all-agriculture index, t-1 to t. y is log harvested-area or yield growth, t to t+1. Prior outcome log growth t-1 to t is controlled. Require finite positive observations and abs(x), abs(prior y), abs(forward y) <=0.50. Only countries with >=5 complete years remain. OLS includes country and treatment-year fixed effects; CR1 country-cluster standard errors use two-sided t(G-1). No fallback estimator or proxy is allowed.

Each cell requires >=500 complete country-years in >=30 countries, >=100 material exposure years with |x|>=0.05 in >=20 countries, a full-rank design, finite positive clustered SE and no country providing >20% of residualized exposure sum of squares. Failure is INCONCLUSIVE. A positive coefficient >=0.05 and two-sided p<=0.00125 is SUPPORTED; a negative coefficient <=-0.05 at the same cutoff is REFUTED; other estimable cases are PARTIAL. Coefficient 0.05 means about 0.5% later log growth for a 10% relative-price increase. All eight remain in the Bonferroni denominator, including failures. Family alpha is 0.01; archive-wide selection remains unadjusted.

This is predictive calibration, not a causal estimate. Price may respond to same-year harvest shocks or anticipation; group aggregation and estimation flags further limit interpretation. Zero causal, policy, school, position and featured credit.

## Official source documentation

- FAO Agricultural producer prices dataset and methodology: https://data.fao.org/catalog/dataset/47c17894-8ca1-4bd0-ba4d-6078e919e9b1 and https://files-faostat.fao.org/production/PP/PP_e.pdf
- FAO crop production, yield and harvested-area dataset: https://data.fao.org/catalog/iso/d24a448b-3b62-4c09-8c1d-4a39bb599876
- FAO statistical database terms (attribution and use conditions): https://www.fao.org/contact-us/terms/db-terms-of-use/en
