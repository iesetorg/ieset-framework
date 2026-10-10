# Prospective omnibus registration: nominal depreciation and HICP consumer-group inflation

**Public hypothesis:** `bis_neer_hicp_multicategory_pass_through_2026`
**Family ID:** `bis_neer_eurostat_goods_hicp_2026_10_10`

**Registration boundary:** Only BIS nominal-EER exposure values, whole-file hashes/manifests, and exact Eurostat HICP categorical COICOP/country/year keys were examined. No selected HICP numeric value, null mask, cell flag, coefficient, or exact-pair fit was opened. The twenty groups and one omnibus rule are frozen before the shared first-addition commit; a narrow source lock is committed separately afterward and before `--run`.

## One question and twenty planned estimates

BIS nominal broad EER depreciation in year `t` may raise local-currency imported-goods and traded-input costs. Does this predict higher **next-year** annual-average HICP inflation in at least **five** of twenty fixed, mutually non-nested household-spending groups, with **no** qualified opposite-direction group? The BIS index rises on appreciation; exposure here is `100 log(mean EER(t−1) / mean EER(t))`, positive for depreciation. Eurostat `RCH_A_AVG` is annual-average inflation in percentage points, not December-to-December inflation. This is one public descriptive hypothesis, not twenty. [BIS methodology](https://data.bis.org/topics/EER), [Eurostat annual table](https://ec.europa.eu/eurostat/databrowser/view/prc_hicp_aind/default/table).

All twenty selected COICOP codes are distinct three-digit groups; none is a prefix of another. Their baskets differ in import share, regulation and service content, and their prices share shocks. No parent aggregate, duplicate category or category×country expansion is a separate test.

| COICOP | Planned group | Key-only cells / countries | Material `|depreciation|≥2` cells / countries |
| --- | --- | ---: | ---: |
| `CP011` | food | 489 / 29 | 206 / 29 |
| `CP012` | non-alcoholic beverages | 489 / 29 | 206 / 29 |
| `CP021` | alcoholic beverages | 489 / 29 | 206 / 29 |
| `CP022` | tobacco | 489 / 29 | 206 / 29 |
| `CP031` | clothing | 489 / 29 | 206 / 29 |
| `CP032` | footwear | 489 / 29 | 206 / 29 |
| `CP045` | electricity, gas and other fuels | 489 / 29 | 206 / 29 |
| `CP051` | furniture and furnishings, carpets and other floor coverings | 489 / 29 | 206 / 29 |
| `CP052` | household textiles | 489 / 29 | 206 / 29 |
| `CP053` | household appliances | 489 / 29 | 206 / 29 |
| `CP054` | glassware, tableware and household utensils | 489 / 29 | 206 / 29 |
| `CP055` | tools and equipment for house and garden | 489 / 29 | 206 / 29 |
| `CP061` | medical products, appliances and equipment | 489 / 29 | 206 / 29 |
| `CP071` | purchase of vehicles | 489 / 29 | 206 / 29 |
| `CP072` | operation of personal transport equipment | 489 / 29 | 206 / 29 |
| `CP091` | audio-visual, photographic and information processing equipment | 489 / 29 | 206 / 29 |
| `CP092` | other major durables for recreation and culture | 450 / 27 | 193 / 27 |
| `CP093` | other recreational items and equipment, gardens and pets | 489 / 29 | 206 / 29 |
| `CP095` | newspapers, books and stationery | 489 / 29 | 206 / 29 |
| `CP123` | personal effects n.e.c. | 489 / 29 | 206 / 29 |

The exact key-only category roster is `data/pinned_evidence/bis_neer_eurostat_goods_hicp_2026_key_roster.csv`, SHA-256 `9548cf5bedc596a978c471ef3b1d69c6338b4a2caffe255507def0ed26e8faa6` (9,741 category-country-treatment-year rows). HICP keys are only an upper bound: no selected outcome values or missingness were screened. Nineteen groups have 489 candidate cells/29 countries and 206 material cells/29; CP092 has 450/27 and 193/27. The 29-country crosswalk, including Eurostat `EL` to BIS `GR`, is frozen in the runner.

## Exact pinned custody

| Role | Vintage and SHA-256 | Fetch manifest and SHA-256 |
| --- | --- | --- |
| neer | `data/vintages/bis/WS_EER@2026-07-23T151604Z.parquet` `57bbce3e22fc428c8cd8ddee8a998d273b5240a816af89e532b81d41ade35170` | `data/manifests/fetch_run_2026-07-23T151632Z.yaml` `1768f0d7c38c93f1ad4df591b0b1634b3460faa964f6267874b8798b7b8dbb81` |
| hicp | `data/vintages/eurostat/prc_hicp_aind@2026-04-30T115920Z.parquet` `be97a646f95e04c481c583bcde08817aaf6fc315cb7b5f1b628c735cf6a2aec4` | `data/manifests/fetch_run_bootstrap_2026-04-30T121833Z.yaml` `e4eba4196e874aa69112f5e93420aa1daeffe64225e73ff536b336e33dec282e` |

The runner checks full-file hashes, exact publisher/series/path/hash manifest entries, bytes and first-addition commit of all five registration files, separate descendant source-lock commit, and absence of measured artifacts in both commits. The HICP source is Git-ignored and copied byte-for-byte into this isolated checkout; it is already present in the main workspace. No machine-local path is committed.

## Frozen sample and estimator

- Exposure years `t=2002..2018`; outcome years `t+1=2003..2019`, before COVID-19. BIS exposure requires `FREQ=M`, nominal `EER_TYPE=N`, broad `EER_BASKET=B`, `OBS_STATUS=A`, twelve finite positive monthly values in both adjacent years, and `|100 log(mean EER(t−1)/mean EER(t))|≤15`. Material exposure has absolute value at least 2.
- Eurostat selector is exact `freq=A`, `unit=RCH_A_AVG`, named `coicop`, national `geo_code`, and year `t+1`. After source lock only, require finite selected HICP values. No outcome trim, parent-category substitution, interpolation or nearby-year match. The pinned Parquet has no retained cell flags, so no break-screened continuity is claimed.
- For each group separately, OLS estimates year `t+1` inflation on year `t` nominal depreciation with country and treatment-year fixed effects. Two-way country/year CR1 covariance uses two-sided Student `t` with `min(G,T)−1` degrees of freedom. No control or lag search after registration.
- Each component needs ≥400 complete cells/24 countries, ≥150 material-depreciation cells/22 countries, and ≥10 complete years per retained country. The measured-panel residualized EER exposure may put ≤30% of squared residual variation in its top 1% of rows and ≤25% in any country. Rank and two-way uncertainty must be valid. Key-only exposure shares are 22.1%/19.2% for nineteen groups and 23.5%/20.3% for CP092; these are **not** measured-panel checks.

## Family correction and one omnibus verdict

All twenty components remain in the denominator, including inconclusive ones. Family alpha **0.01** gives Bonferroni two-sided **p≤0.0005** per component. A positive component additionally needs beta ≥ **+0.04 HICP percentage points per +1 log-percentage-point depreciation** and every leave-one-country-out beta ≥ **+0.02**. A qualified opposite component needs beta ≤ **−0.04**, the same p cutoff, and every country-deletion beta ≤ **−0.02**. Other estimable components are partial.

Only **one** public verdict is formed: `INCONCLUSIVE` if fewer than **16** components are estimable; `SUPPORTED` if at least **5** components qualify positive and **none** qualifies opposite; `REFUTED` if at least **5** qualify opposite and **none** qualifies positive; `PARTIAL` otherwise. Twenty component rows are disclosed as diagnostics, never as separate hypothesis IDs, graduations, policy claims or independent replications. The same category cannot count twice.

## Prior work, limitations and chronology

IESET already has BIS EER to headline inflation studies. A source/claim scan found no exact test of this fixed twenty-group, five-group omnibus. It was selected after archive-wide exploration, not an independent holdout. The local Bonferroni rule does not correct archive-wide selection. Euro-area common currency movements, commodity prices, excise taxes, domestic demand, monetary responses, quality adjustments and pricing-to-market remain confounds. Some groups contain locally delivered services or regulated prices. Every verdict has **zero causal, policy, school-score, position and featured credit**.

1. Commit this audit, one YAML spec, one steelman, the key-only roster and guarded runner **together**. No result or source lock in this first-addition commit.
2. Invoke `--write-source-lock` and commit its narrow JSON as a separate descendant, with no measured result.
3. Only then invoke `--run`, commit the single omnibus run with all twenty component estimates, and invoke `--verify` for exact replay before index regeneration.
