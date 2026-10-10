# Blind SIPRI military burden and later UNDP components preregistration

One four-cell descriptive family was fixed before selected military-share or UNDP values, null masks or fits were opened. Source manifest metadata, hashes, schemas, country/year keys and official methods were inspected. The four components overlap and are not independent replications.

Key roster `data/pinned_evidence/sipri_undp_military_burden_2026_key_roster.csv` has SHA-256 `ae96b3af522e07ff24f42178ea70dd640ef8d5635df0b0d3f8b658141668a8ae`. Source-key opportunities do not establish measured complete cases.

| Outcome | Key rows | Countries |
| --- | ---: | ---: |
| life_expectancy | 3818 | 166 |
| mean_years_schooling | 3565 | 164 |
| expected_years_schooling | 3654 | 165 |
| gni_per_capita | 3738 | 165 |

## Source custody

All five ignored local Parquets are pinned below and match tracked fetch-manifest entries. The SIPRI vintage is the Share of GDP sheet of a 2023-ending workbook, while the UNDP vintage is the 2025 HDR component time series. Licensed raw values are not committed. Exact replay requires matching local files. The SIPRI local Parquet has no retained observation-quality flags.

| Role | Relative path | SHA-256 | Manifest |
| --- | --- | --- | --- |
| military_burden | `data/vintages/sipri/milex_share_gdp@2026-04-30T114417Z.parquet` | `5ccce854cc3127eb0510b2f9f0e99741fb4a037a5950c745137970e7c618d3be` | `data/manifests/fetch_run_bootstrap_2026-04-30T121833Z.yaml` |
| life_expectancy | `data/vintages/undp_hdi/life_expectancy@2026-05-05T204045Z.parquet` | `13b99319b8b1a2be96f0774dfd67104e2b7a41b4ca176bf43486b65ff99f43cb` | `data/manifests/fetch_run_2026-05-05T210519Z.yaml` |
| mean_years_schooling | `data/vintages/undp_hdi/mean_years_schooling@2026-05-05T204045Z.parquet` | `e3a1e5a17bf361219f2a13a1e5e4b6c5cc0faa28c620245a907f2e087a725449` | `data/manifests/fetch_run_2026-05-05T210519Z.yaml` |
| expected_years_schooling | `data/vintages/undp_hdi/expected_years_schooling@2026-05-05T204045Z.parquet` | `86c0f5c46556a914fa8bc72405fa46ad9e8de550612d03795531d2d196d5735f` | `data/manifests/fetch_run_2026-05-05T210519Z.yaml` |
| gni_per_capita | `data/vintages/undp_hdi/gni_per_capita@2026-05-05T204045Z.parquet` | `9f9c6a839567dcfa4dd3f51876f8e76755e5bddff3d5539ba0cd077d618f30a0` | `data/manifests/fetch_run_2026-05-05T210519Z.yaml` |

## Frozen design and failure gates

Exposure years t=1994..2016; x is the SIPRI military-expenditure share of GDP (percentage points) at t minus t-3. Every outcome is its UNDP value change from t to t+3; GNI per person uses 100 × log ratio. Prior outcome change t-3 to t is controlled. Exact years only; no pandemic period enters the outcome. The explicit name crosswalk and pycountry conversion exclude aggregate and predecessor-state rows. Shares must be finite and 0..40, with |x|≤3. Outcome-specific three-year absolute bounds are 8 life years, 5 mean schooling years, 5 expected schooling years and 100 log points of GNI. Countries need at least six complete years.

Each cell requires at least 900 complete rows/60 countries and at least 100 material rows/30 countries with |x|≥0.25 percentage points. The country and treatment-year fixed-effect OLS with prior outcome change must be full rank, finite clustered SE, and no country can exceed 15% of residualized exposure sum of squares. Failure is INCONCLUSIVE. A negative beta meeting the cell's fixed practical magnitude and two-sided p≤0.0025 is SUPPORTED; an equally strong positive beta is REFUTED; other estimable cells are PARTIAL. Four cells remain in the family denominator even if one fails. Family alpha is 0.01. No wider archive-search correction is claimed.

This is an observational predictor test, not an estimate of spending tradeoffs or a military policy effect. War, threats, crises, recession denominators, fiscal composition and common development trends are unresolved. Overlapping windows and revised/modelled inputs add uncertainty. All cells have zero causal, policy, school, position and featured credit.

Official source documentation: https://www.sipri.org/databases/milex/sources-and-methods and https://hdr.undp.org/data-center/documentation-and-downloads
