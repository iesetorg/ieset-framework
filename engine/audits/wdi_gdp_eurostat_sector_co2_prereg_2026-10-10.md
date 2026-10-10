# Prospective twelve-test registration: GDP cycle and sector CO2

**Family ID:** `wdi_gdp_eurostat_sector_co2_2026_10_10`
**Registration boundary:** Only WDI real-GDP-growth exposure values, whole-file
hashes/manifests, and exact Eurostat categorical gas, sector, country, and
year **keys** were examined. No selected Eurostat CO2 value, null mask,
cell flag, coefficient, or model was opened. Every sector and threshold is
frozen here before the shared first-addition commit; a narrow source lock
must be committed separately afterward and before `--run`.

## Question and sector integrity

For each listed non-nested UNFCCC Common Reporting Format source category,
is real GDP growth in calendar year `t` associated with higher **same-year**
direct fuel-combustion CO2 growth, `log(CO2(t)/CO2(t−1))`, across the fixed
European national panel? WDI growth is an aggregate macro cycle, not
sectoral output or a policy intervention. The response is a territorial
inventory source, not a NACE industry measure or consumption footprint.
The prediction is a within-country descriptive association, with no causal
or forward-lag claim. [Eurostat dataset](https://ec.europa.eu/eurostat/databrowser/view/env_air_gge/default/table),
[Eurostat metadata](https://ec.europa.eu/eurostat/cache/metadata/EN/env_air_gge_esms.htm).

These twelve categories are mutually non-nested leaves or residual leaves
within the fuel-combustion inventory hierarchy. No parent aggregate,
additional gas, or gas×sector cross-product appears as a separate test.
For manufacturing, these are **fuel** emissions only; process emissions
are recorded elsewhere.

| CRF code | Fixed source category | Key-only candidate pairs / countries | Material `|GDP growth|≥1` pairs / countries |
| --- | --- | ---: | ---: |
| `CRF1A1A` | Public electricity and heat | 664 / 29 | 575 / 29 |
| `CRF1A2A` | Iron and steel | 664 / 29 | 575 / 29 |
| `CRF1A2C` | Chemicals | 664 / 29 | 575 / 29 |
| `CRF1A2D` | Pulp, paper and print | 664 / 29 | 575 / 29 |
| `CRF1A2E` | Food, beverages and tobacco | 664 / 29 | 575 / 29 |
| `CRF1A2F` | Non-metallic minerals | 664 / 29 | 575 / 29 |
| `CRF1A2G` | Other manufacturing and construction | 664 / 29 | 575 / 29 |
| `CRF1A3A` | Domestic aviation | 663 / 29 | 574 / 29 |
| `CRF1A3B` | Road transport | 664 / 29 | 575 / 29 |
| `CRF1A4A` | Commercial and institutional | 664 / 29 | 575 / 29 |
| `CRF1A4B` | Residential | 664 / 29 | 575 / 29 |
| `CRF1A4C` | Agriculture, forestry and fishing **fuel** | 664 / 29 | 575 / 29 |

The key-only roster is
`data/pinned_evidence/wdi_gdp_eurostat_sector_co2_2026_key_roster.csv`,
SHA-256 `2c5b22762e26f303500ce5840daa5d7839f9e172c83f98b220be83323fe9e96c`
(7,967 sector-country-year rows). These counts are only upper bounds:
Eurostat outcome values and their missingness have not been checked.
The 29-country crosswalk and all twelve sector codes are constants in
the frozen runner.

## Exact pinned custody

| Role | Relative vintage and SHA-256 | Fetch manifest and SHA-256 |
| --- | --- | --- |
| GDP exposure | `data/vintages/world_bank_wdi/NY.GDP.MKTP.KD.ZG@2026-05-05T194655Z.parquet` `db76a52909929c6cd3ca1dd3d1fdc4b28d28cbaea92e16cb59e88ee53d3f2e58` | `data/manifests/fetch_run_2026-05-05T200056Z.yaml` `a571d660fd359d245176b77e595b59923a90a1e40a799ea56c13f001a7b09945` |
| Sector CO2 outcome | `data/vintages/eurostat/env_air_gge@2026-04-30T115534Z.parquet` `5597d4f1a75c8c9a91306723772bc8ce4e3df3cfa9af65ce137bc6a3e52d8ba2` | `data/manifests/fetch_run_bootstrap_2026-04-30T121833Z.yaml` `e4eba4196e874aa69112f5e93420aa1daeffe64225e73ff536b336e33dec282e` |

The runner checks full file hashes, exact publisher/series/path/entry hashes,
registration bytes, separate descendant source-lock commit, and absence of
results in both registration and lock commits. The Eurostat source is copied
byte-for-byte into this isolated worktree; only the authored runner,
preregistration, roster, specifications, and steelmen are added to Git.
No machine-local path is committed.

## Frozen sample and measurement limits

- Annual exposure years `t=1996..2018`, excluding COVID-19 years. WDI
  `NY.GDP.MKTP.KD.ZG` must be finite and within ±15 percentage points.
  A material exposure year has `|growth|≥1` point.
- Eurostat selector must be exact `freq=A`, `unit=THS_T`, `airpol=CO2`,
  the named `src_crf`, and one of the 29 fixed national `geo_code` values.
  Require category keys at both `t−1` and `t`. There is no interpolation,
  aggregate replacement, nearest-year match, or gas/sector switch.
- After the source-lock commit only, require both selected CO2 values
  finite and strictly positive for the log change. Do not trim by the
  observed change magnitude. Keep only countries with at least ten
  **complete** annual pairs.
- The pinned Eurostat Parquet retains no cell flags. Eurostat says its EEA
  inventory zero can mean either “not occurring” or “included elsewhere”;
  the log rule excludes nonpositive endpoints without asserting which
  meaning applies. No cell is described as break-screened. WDI status is
  blank and cannot certify macro-series method continuity.

## Frozen estimator, floors, and verdicts

Each case separately estimates OLS of same-calendar-year log sector CO2
change on the WDI real-GDP-growth percentage points, country fixed effects,
and calendar-year fixed effects. Country-cluster CR1 uncertainty uses a
two-sided Student `t` with `G−1` country degrees of freedom. Report the
`1−0.01/12` confidence interval. No controls, lags, window selection, or
sector-specific estimators can be added after outcome access.

Each test requires at least **450** complete pairs across **23** countries,
**350** material-growth pairs across **23** countries, and **ten** complete
annual pairs per retained country. Residualized GDP-growth variation on
the fitted sample may place at most **30%** of squared residual exposure
in the top 1% of rows and **20%** in any country. Require full model rank
and finite positive cluster uncertainty.

All twelve tests stay in the denominator even if any one fails. Family
alpha is **0.01**, two-sided Bonferroni **p≤0.0008333333** per sector.
`SUPPORTED` requires beta at least **+0.005 log CO2 point per +1 GDP-growth
percentage point** and the p cutoff. `REFUTED` requires beta at most
**−0.005** with the same cutoff. Any other estimable relation is `PARTIAL`;
source, chronology, coverage, variation, rank, or uncertainty failure is
`INCONCLUSIVE`. A support verdict is a descriptive pro-cyclicality signal,
not a sectoral production or policy effect.

## Prior work and credit

The IESET corpus contains EU decoupling studies and a WDI renewable-share/
electric-use family against the **power/heat** CO2 source, but a source/claim
scan found no exact WDI GDP-growth to same-year log CO2 change test for
these twelve separately named CRF categories. That scan is not an
independent holdout; the family was chosen after broader corpus work.
These sectors share macro shocks and inventory revisions, and the local
Bonferroni rule does not correct archive-wide selection. Energy prices,
weather, regulation, technologies, trade and offshoring confound the
relation. All verdicts have **zero causal, policy, school-score, position,
and featured credit**.

## Required chronology

1. Commit this audit, all twelve YAML specs and steelmen, the key-only
   roster, and guarded runner **together**. No result artifacts in that
   commit.
2. Invoke `--write-source-lock` and commit the narrow JSON as a separate
   descendant, again with no measured result.
3. Only then invoke `--run` and commit every verdict, including failed
   sectors. Invoke `--verify` for exact replay before index regeneration.
