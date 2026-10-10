# Preregistration: applied tariff declines and later export diversity

**Status: blind registration package.** This is one three-cell descriptive family. The World Bank/WITS source definitions, schema, categorical keys, tariff and GDP-control values, and exact WITS country/year keys were screened. No selected WITS export-count or HHI values, null patterns, estimates, or result cards were opened for this design. The three specs, steelmen, key roster, and guarded runner must first appear together in one commit. A narrow source lock must be committed in a later descendant commit before the runner can open selected export values.

## Distinct measured questions

For reporter economy c and treatment year t from 2000 through 2016, define `D(c,t) = weighted applied merchandise tariff(c,t-3) - tariff(c,t)` in percentage points. Positive D is a decline, not a treaty event or randomly assigned reform. Compare D with a later `t` to `t+3` change in (1) log1p exported HS6 category count, (2) a **decline** in export-market HHI, or (3) a **decline** in export-product HHI. Higher values of each oriented outcome indicate greater breadth/diversity. These are three distinct outcomes, not three independent confirmation studies. The last outcome endpoint is 2019, before the pandemic. The export-product source uses mirrored Comtrade data and has no method-break status field.

The local `wits:product_concentration` label is misleading: its indicator code is `HH-MKT-CNCNTRTN-NDX`, and the pinned rows say `HH Market concentration index`. It measures concentration across destination **markets**. The distinct `wits:export_product_hhi_wits` file measures concentration across export **products**. The World Bank WITS API describes market HHI and exported-product counts separately; the [World Bank product-HHI catalog](https://datacatalog.worldbank.org/search/dataset/0064718/herfindahl-hirschman-product-concentration-index-export) defines the latter and its public CC BY 4.0 terms. The [World Bank tariff glossary](https://databank.worldbank.org/metadataglossary/world-development-indicators/series/TM.TAX.MRCH.WM.AR.ZS/~/home) defines the import-weighted applied rate and its coverage limits.

| Role | Selected immutable vintage SHA-256 | Fetch manifest SHA-256 |
| --- | --- | --- |
| Tariff | `data/vintages/wits/weighted_mean_applied_tariff@2026-07-23T151540Z.parquet` `73520e0da6a44048e51a64671c97369aadf160130937f351f90375fb86b0e010` | `data/manifests/fetch_run_2026-07-23T151550Z.yaml` `96243db0b85df0b1d5ccd10631b356618a9372d62c4741b692129658a49e05a5` |
| GDP per person | `data/vintages/world_bank_wdi/NY.GDP.PCAP.KD@2026-05-05T194645Z.parquet` `0cf53ee3a334988ded027fbe160a8d8c70773656772daf1c82206eb3f7c02a9f` | `data/manifests/fetch_run_2026-05-05T200056Z.yaml` `a571d660fd359d245176b77e595b59923a90a1e40a799ea56c13f001a7b09945` |
| Exported HS6 count | `data/vintages/wits/unique_hs6_products@2026-07-23T153652Z.parquet` `29db44b85d263bfc92307182b19f3baf4073dae446e5c3af37d82a284bfb2934` | `data/manifests/fetch_run_2026-07-23T153659Z.yaml` `542aacbcc80b1856262eda14f37d0532c7a14611c8b9d698ab516529942d0b73` |
| Export-market HHI | `data/vintages/wits/product_concentration@2026-07-23T151543Z.parquet` `c59b180e07f484546e131fa6a4f47a725ecc790effbb3d395e5d2c4e36381949` | same tariff manifest |
| Export-product HHI | `data/vintages/wits/export_product_hhi_wits@2026-05-16T094546Z.parquet` `88528dd4d46c0efebc928f2c4c3ac63d2b60bee5505d313184342b8e071b7d47` | `data/manifests/fetch_run_wits_export_product_hhi_2026-05-16T094546Z.json` `280a99ce5e9458f55b28009ec089b5b258600381524c53c880eeb9a67a09dd69` |

The final lock must contain only these five selected source entries, their exact hashes, the registration commit, the key roster, and the source-only preflight. It must not copy every entry in the whole fetch manifests. The raw Parquets are ignored in the clean worktree; byte-identical copies from the main local cache are required for lock and replay. The manifest files are tracked.

## Key-only roster and frozen model

`data/pinned_evidence/wits_tariff_export_diversity_key_roster_2026.csv` has SHA-256 `c0d49eac18fbc53fc1a26bb6426a7e3d090f123e1953d805fc6937c6854ce327`, columns `case,country_iso3,year`, sorted by fixed case, code, and year. The registration-time allowlist is `pycountry` 24.6.1 current ISO3, including some reporter territories; this is a reporter-economy panel, not exclusively sovereign states. Replay uses the frozen roster, not a fresh allowlist. The tariff and WDI control must each have finite values at t-3 and t, tariff source status blank, GDP/person positive and status blank. The WITS outcome must have categorical keys at t-3, t, and t+3. Category selectors are exported HS6 count `WLD/999999/NMBR-XPRT-HS6-PRDCT`, market HHI `999/999999/HH-MKT-CNCNTRTN-NDX`, and product HHI `WLD/H0/Tier3`. All selected key slices are unique by reporter/year.

| Fixed case | Key-only upper-bound rows | Reporter economies | Material tariff declines ≥2 pp | Material increases ≥2 pp |
| --- | ---: | ---: | ---: | ---: |
| Exported HS6 count | 1,721 | 157 | 321 / 105 economies | 90 / 51 |
| Export-market HHI | 1,734 | 157 | 323 / 105 | 91 / 51 |
| Export-product HHI | 1,712 | 158 | 320 / 105 | 87 / 51 |

These are upper bounds: no export outcome value or missingness has been read. Following source lock, require nonnegative integral counts for HS6; HHI must be finite in [0,1]. Drop only invalid selected triples, then reporter economies with fewer than five complete treatment years. No imputation, custom trimming, endpoint change, or case replacement is permitted. The complete sample must have at least 1,000 rows and 90 reporters, 200 material tariff declines in 70 reporters, and 45 material increases in 25 reporters. Failure makes that cell INCONCLUSIVE. Values from an invalid source selector or mismatched hash make the entire family INCONCLUSIVE.

For each case, regress the oriented t-to-t+3 outcome on D, the selected outcome's level at t, its oriented t-3-to-t change, log real GDP/person at t, prior log GDP/person change, reporter effects and treatment-year effects. For the count use log1p on all outcome levels; HHI outcomes use raw [0,1] points. OLS uses reporter-cluster CR1 uncertainty, two-sided Student t(G-1) inference, and a 99% confidence interval. The design must be full rank with finite positive uncertainty. Residualize D against every other covariate and fixed effect on the complete sample; the top 1% of rows may contribute at most 30% of squared residual treatment variation and the top reporter at most 20%. Exceeding either makes the cell INCONCLUSIVE.

The three-cell family uses Bonferroni two-sided p≤0.01/3. For exported count, the practical threshold is 0.01 log1p-count point per tariff percentage point; for each HHI decline it is 0.005 HHI point per tariff percentage point. Positive coefficients meeting both size and p gates are SUPPORTED descriptive associations; equally large negative coefficients meeting p are REFUTED; other estimable cases are PARTIAL. All three verdicts and failures must be retained. The correction covers only these fixed tests, not the full IESET archive search.

## Limits and execution

Import-weighted tariff changes can come from the weight denominator, product composition, changing tariff schedules, or data revisions. Export diversity can move with currency, commodity cycles, foreign demand, infrastructure, trade agreements, income, and reporting. The first two WITS API outcomes have no observation-status/method-break field; the product-HHI series is mirrored rather than direct country reports. Pretrend adjustment may absorb a real channel. Country clustering cannot make overlapping three-year windows independent. Earlier WITS/CEPII and tariff-structure work is visible, so this family is no archive-wide independent holdout. Every verdict has **zero causal, policy-effect, school-score, school-position, and featured credit**.

1. Commit the three specs, steelmen, roster, this plan, guarded runner, and synthetic contract tests together; do not read selected WITS outcomes.
2. Supply byte-identical ignored raw files, run `--preflight`, create a narrow `--lock`, then commit that lock separately with ancestry from the registration.
3. Only then run the three fixed cases, write standard evidence packets, run exact replay, and refresh the public audit/indexes only for eligible measured results. Keep any INCONCLUSIVE cases archived.
