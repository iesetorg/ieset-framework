# Eurostat regional R&D four-cell preregistration — 2026-10-10

This family freezes four substantive combinations: business or government performance of R&D, each against later real total-GVA growth or later total-unemployment change. These are two mechanisms and two outcomes using overlapping regions and years, not four independent policy events. No selected value, outcome-null mask, coefficient or sign was inspected before this registration.

Key roster: `data/pinned_evidence/eurostat_regional_rd_forward_2026_key_roster.csv`; SHA-256 `789ec757b0a0fecb3043716af387c0cf571fe1c09bd2f02d1566452fcf031f59`. It was built only from categorical selectors, region codes and years. Four-cell denominator and every failed cell remain in the result ledger.

| Case | Key region-years | Regions | Country prefixes |
| --- | ---: | ---: | ---: |
| `eurostat_business_rd_next_year_real_gva_growth_2026` | 1,869 | 99 | 20 |
| `eurostat_business_rd_next_year_unemployment_change_2026` | 2,472 | 141 | 24 |
| `eurostat_government_rd_next_year_real_gva_growth_2026` | 2,380 | 130 | 21 |
| `eurostat_government_rd_next_year_unemployment_change_2026` | 2,913 | 171 | 25 |

Raw sources are present in the read-only main checkout and byte-matched to the tracked fetch manifest. The source lock will be committed separately before reading selected values.

- R&D by performance sector, `PC_GDP`: `data/vintages/eurostat/rd_e_gerdreg@2026-04-30T115929Z.parquet` SHA-256 `f0602b04f2eb4a610f8d986097ccbab59d0b07cab709826dc8f89dffbd97b51f`.
- Real GVA growth is constructed from next-year previous-year-price (`PYP_MEUR`) total GVA and current-price (`CP_MEUR`) total GVA at the prior year, avoiding nominal-current-price growth. `data/vintages/eurostat/nama_10r_3gva@2026-04-30T115907Z.parquet` SHA-256 `d10b38100e344d4eb486d8380e51f645ce4fc3b425c0235f05af3a731495358f`.
- Total unemployment, sex T, Y15-74, education TOTAL, unit PC: `data/vintages/eurostat/lfst_r_lfu3rt@2026-04-30T115837Z.parquet` SHA-256 `8244ec97ea2f8e5117e81433299d2dfc855f4f0343824f6c572b129007ef86b7`.
- Tracked fetch manifest: `data/manifests/fetch_run_bootstrap_2026-04-30T121833Z.yaml`.

The key screen excludes EA/EU aggregate codes and uses four-character alphabetic-prefix, non-Z NUTS2-like codes and at least eight candidate exposure years. Eurostat may revise NUTS boundaries while preserving or replacing a code. A separate geography-continuity review is required before result interpretation; code length alone is not territorial stability. Region-year observations within a country and within one region are dependent. The fixed estimator uses region and country-year effects with region-cluster inference; influence limits and leave-three-largest-country checks are frozen.

Complete-case, material-exposure, residual-variation, region/country concentration, estimator and source-custody gates in each YAML are dispositive. Support or refutation additionally requires the frozen meaningful slope, two-sided family Bonferroni p<=0.0025, and sign stability under three country omissions. Failed cells remain INCONCLUSIVE. Valid nonsignificant or sub-material cells remain PARTIAL. All cells have zero causal, policy, school, position and featured credit.
