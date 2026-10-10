# Prospective registration: merchandise tariff declines and later goods prices

**Public hypothesis:** `wits_tariff_decline_goods_hicp_forward_2026`  
**Family:** `wits_tariff_eurostat_goods_hicp_2026_10_10`  
**Status:** blind registration package. The World Bank/WITS tariff values and Eurostat categorical COICOP/country/year keys were inspected. No selected HICP value, null mask, flag, coefficient, or exact-pair fit was opened. Six components form one hypothesis.

## Sources and question

The World Bank's [indicator glossary](https://databank.worldbank.org/metadataglossary/world-development-indicators/series/TM.TAX.MRCH.WM.AR.ZS) defines `TM.TAX.MRCH.WM.AR.ZS` as applied merchandise tariff rates weighted by partner/product import shares, including rate substitutions and import-weight shifts. It is an **all-products rate**, not a clothing, appliance or vehicle tariff, and a change is not a law event. [Eurostat's annual HICP table](https://ec.europa.eu/eurostat/databrowser/view/PRC_HICP_AIND__custom_7002518/default/table?lang=en) defines `RCH_A_AVG` as the inflation rate comparing one calendar year's average of monthly indices with the previous year's average. [Eurostat HICP documentation](https://ec.europa.eu/eurostat/web/hicp/information-data) explains the hierarchical COICOP groups and that the old `prc_hicp_aind` table was superseded under ECOICOP version 2 in 2026. This study pins the old table's April 2026 vintage and stops before COVID-19.

For country `c` and treatment year `t=1998..2018`, define `D(c,t) = tariff(c,t-3) − tariff(c,t)` in percentage points. Positive `D` denotes a three-year decline. For each fixed group, regress published HICP annual-average inflation in `t+1=1999..2019` on `D`. A negative coefficient is the proposed descriptive direction. Six distinct three-digit goods-heavy spending groups were selected before price values were opened: clothing `CP031`, footwear `CP032`, household textiles `CP052`, household appliances `CP053`, vehicle purchases `CP071`, and audio-visual/information equipment `CP091`. Their **actual import shares were not measured**, and their prices share country shocks. A result is never category-specific tariff pass-through or a policy effect.

| Role | Immutable local vintage SHA-256 | Fetch manifest SHA-256 |
| --- | --- | --- |
| WITS tariff | `data/vintages/wits/weighted_mean_applied_tariff@2026-07-23T151540Z.parquet` `73520e0da6a44048e51a64671c97369aadf160130937f351f90375fb86b0e010` | `data/manifests/fetch_run_2026-07-23T151550Z.yaml` `96243db0b85df0b1d5ccd10631b356618a9372d62c4741b692129658a49e05a5` |
| HICP | `data/vintages/eurostat/prc_hicp_aind@2026-04-30T115920Z.parquet` `be97a646f95e04c481c583bcde08817aaf6fc315cb7b5f1b628c735cf6a2aec4` | `data/manifests/fetch_run_bootstrap_2026-04-30T121833Z.yaml` `e4eba4196e874aa69112f5e93420aa1daeffe64225e73ff536b336e33dec282e` |

The two Parquets are Git-ignored, byte-identical local copies from the main source cache. The source lock will pin the two selected entries, the registration commit, and the exact key-only preflight. It will be committed separately before opening HICP values. The Eurostat manifest says CC BY 4.0; the WITS manifest says World Bank WITS terms / World Bank API CC BY where mirrored. The source rights and existing repository-history publication hold remain separate release decisions. No raw values are placed in tracked output.

## Blind sample envelope and frozen rules

The key-only roster `data/pinned_evidence/wits_tariff_hicp_key_roster_2026.csv` has **3,084** sorted rows (`coicop,geo_code,treatment_year`), SHA-256 `0c10404ea09b28c5017430c9232eda81dc7713f175fde54708493f124609fbe8`. Each group has 514 candidate rows, 33 countries and 21 treatment years; 71 rows in 30 countries have absolute tariff change at least 1 percentage point. These are upper bounds, not measured outcome completeness. The frozen Eurostat-to-ISO3 crosswalk uses national codes only (including `EL→GRC` and `UK→GBR`); no EU aggregate enters.

Before registration, **treatment-only** influence screening found that without a cap, the top 1% of rows carried 37.0% and the largest country 27.3% of squared country/year-residualized tariff variation. A prespecified `|D|≤6` cap leaves 514 key rows per group and reduces those key-only shares to 27.8% and 13.5%. This is a design response to observed exposure concentration, **not** HICP-driven trimming. All six groups use the same cap. No selected HICP value or missingness was read.

After source lock only, keep finite exact HICP cells. Reapply a minimum of five complete years per country. Each component needs at least 400 rows/28 countries and at least 50 absolute tariff changes ≥1 point across 25 countries. The measured complete-case residualized `D` may place at most 30% of squared variation in the top 1% of rows and 25% in one country. No outcome trim or imputation is permitted. Each component fits country and treatment-year fixed-effects OLS, with two-way country/year CR1 covariance and two-sided Student `t(min(G,T)-1)` inference. Model rank, finite positive variance and leave-one-country-out coefficients must be valid. There are no controls or lag searches.

Six planned components remain in a Bonferroni family at alpha 0.01, so each needs two-sided **p≤0.0016666666667**. A component is `SUPPORTED` if beta ≤ **−0.10** HICP percentage points per +1 tariff-decline point and every country-deletion beta ≤ **−0.05**, as well as the p gate. It is `REFUTED` if beta ≥ **+0.10**, every country-deletion beta ≥ **+0.05**, and p passes. Other estimable components are `PARTIAL`; any component failing frozen data or influence gates is `INCONCLUSIVE`. The **single** omnibus is `INCONCLUSIVE` if fewer than five groups are estimable; `SUPPORTED` if at least two support and none refutes; `REFUTED` if at least two refute and none supports; `PARTIAL` otherwise. All six remain in the denominator even if one fails.

## Interpretation and execution boundary

EU members share an external tariff, while national import weights and reporting can differ. Currency movements, VAT, input costs, distribution margins, demand, accession and other changes can jointly move tariffs and goods prices. Three-year changes overlap in time, and country/year clustering does not make them independent. Existing IESET tariff and HICP work makes this an archive-selected question. The local six-test correction does not correct archive-wide selection. No causal, policy-effect, school-score, position, or featured credit follows any verdict.

1. Commit this plan, the one YAML specification, steelman, key-only roster and guarded runner together, with no selected HICP values or measured artifacts.
2. Run `--write-source-lock` and commit the narrow JSON in a separate descendant commit.
3. Only then run the fixed measured test, retain all six components and the one omnibus result, and run `--verify` for exact replay. Keep an inconclusive omnibus archived.
