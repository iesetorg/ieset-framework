# Prospective two-test registration: real growth and in-work poverty

**Family ID:** `wdi_gdp_eurostat_inwork_poverty_2026_10_10`
**Registration boundary:** WDI treatment values and exact Eurostat selector
keys were examined. No selected Eurostat outcome values, null masks,
coefficient signs, or models were opened before this registration. The
registered files and runner must be committed together, followed by a
separate source-lock commit, before any measured outcome read.

## Questions and timing

1. `wdi_gdp_growth_eurostat_employed_inwork_poverty_forward_2026`: Does
   greater real GDP growth in calendar year `t` predict a lower change in
   the Eurostat in-work at-risk-of-poverty rate for **all employed people**
   aged 18–64 from survey year `t+1` to `t+2`?
2. `wdi_gdp_growth_eurostat_salaried_inwork_poverty_forward_2026`: The same
   prespecified relation for **employees** aged 18–64.

The Eurostat rate is relative to 60% of national median equivalised
household disposable income after transfers. Eurostat says the EU-SILC
income reference year generally precedes the survey year, so the selected
`t+1` and `t+2` survey rates broadly correspond to income years `t` and
`t+1`. UK and Ireland followed historical exceptions and are excluded.
The treatment can affect the baseline income year, and even among remaining
countries income timing and survey methods may differ. Thus the word
“forward” describes the published survey-year endpoints and this study is
strictly descriptive. [EU-SILC metadata](https://ec.europa.eu/eurostat/cache/metadata/en/ilc_sieusilc.htm),
[in-work rate definition](https://ec.europa.eu/eurostat/cache/metadata/en/sdg_01_41_esmsip2.htm).

## Pinned custody

| Role | Relative vintage path | SHA-256 | Fetch manifest and SHA-256 |
| --- | --- | --- | --- |
| WDI growth | `data/vintages/world_bank_wdi/NY.GDP.MKTP.KD.ZG@2026-05-05T194655Z.parquet` | `db76a52909929c6cd3ca1dd3d1fdc4b28d28cbaea92e16cb59e88ee53d3f2e58` | `data/manifests/fetch_run_2026-05-05T200056Z.yaml`, `a571d660fd359d245176b77e595b59923a90a1e40a799ea56c13f001a7b09945` |
| EU-SILC rate | `data/vintages/eurostat/ilc_iw01@2026-04-30T115759Z.parquet` | `100a6bf3f962f53c05133b3e9a7e40f25db36bd03575d3fd7816a4368f1ab246` | `data/manifests/fetch_run_bootstrap_2026-04-30T121833Z.yaml`, `e4eba4196e874aa69112f5e93420aa1daeffe64225e73ff536b336e33dec282e` |

The runner checks whole-file SHA-256 and the exact publisher, series ID,
relative Parquet path, and entry hash in each manifest. The later source
lock is narrow: only these two entries, registration commit ID, and
preflight summary. Raw files may be copied byte-for-byte from the main
checkout into the isolated worktree, then rehashed. No local home-directory
path is committed. Missing or mismatched sources stop the study.

## Frozen sample

- WDI `indicator_id=NY.GDP.MKTP.KD.ZG`; real GDP annual growth in percent,
  calendar year `t=2005..2017`. Keep a unique national ISO3 country-year
  with finite growth and `|growth|≤15` percentage points. This cap uses
  treatment values alone. The WDI status column is blank throughout this
  pinned series and does not certify national-accounts method continuity.
- Within that shared eligibility window, the frozen `EMP` key roster spans
  treatment years 2005–2017 and the frozen `SAL` key roster spans 2008–2017.
- Eurostat `ilc_iw01` exact `freq=A`, `sex=T`, `age=Y18-64`, `unit=PC`,
  and `wstatus=EMP` or `SAL`; national geo codes in the frozen crosswalk.
  Require exact keys for survey years `t+1` and `t+2`. Exclude aggregates,
  UK, and Ireland. Require at least five candidate treatment years per
  country before freezing the roster.
- The committed key-only roster is
  `data/pinned_evidence/wdi_gdp_inwork_poverty_2026_key_roster.csv`, SHA-256
  `f04b873741ed2c47656989a281d9bfca59df2c80fcbdd7f43e00edbadec0f3a5`.
  No outcome value or null mask was accessed to form it. The treatment-only
  residual variation check uses country and treatment-year fixed effects.

| Case | Frozen key pairs / countries | Material `|growth|≥1` pairs / countries | Positive / negative material years | Treatment top 1% / largest country |
| --- | ---: | ---: | ---: | ---: |
| EMP | 383 / 30 | 320 / 30 | 268 / 52 | 18.46% / 12.26% |
| SAL | 298 / 30 | 240 / 30 | 188 / 52 | 17.77% / 13.04% |

The raw selected Eurostat Parquet has `freq, wstatus, sex, age, unit,
geo_code, period, value` only. Neither it nor the committed fetch manifest
contains cell-status or method-break flags. **Prespecified exclusion rule:**
there is no flag-based exclusion on this vintage. After the separate
source-lock commit, each selected endpoint must be a finite rate in
`[0,100]`; invalid or missing endpoints remove the pair, and countries
with fewer than five complete pairs are removed. No visual break check,
external revised flag, outcome-magnitude trimming, interpolation,
nearest-year join, or substitute series may alter the sample. A result
cannot be called break-screened.

## Fixed estimator, gates, and interpretation

For each test separately, regress the rate change in percentage points,
`Y(c,t+2)−Y(c,t+1)`, on WDI real GDP growth in percentage points in `t`.
Use country and treatment-year fixed effects, OLS, country-cluster CR1
uncertainty, and two-sided Student `t` with `G−1` country degrees of
freedom. Report a **99.5% two-sided confidence interval** using
`t(0.9975,G−1)`, matching the family cutoff. No adaptive controls or lags.
Residualized treatment variation on the complete fitted sample must have
at most 30% of its squared sum in the top 1% of rows and at most 20% in
any one country. Require full rank, at least 20 country clusters, and
finite positive cluster uncertainty. The 2008–09 treatment-year exclusion
and baseline-rate adjustment are diagnostics only, incapable of changing
the primary verdict.

| Case | Minimum complete pairs / countries | Minimum material complete pairs / countries |
| --- | ---: | ---: |
| EMP | 280 / 25 | 200 / 25 |
| SAL | 220 / 25 | 160 / 25 |

Both tests remain in one fixed family, even if one becomes inconclusive.
Family alpha is 0.01, with two-sided Bonferroni **p≤0.005** per test.
`SUPPORTED` requires a negative coefficient at or beyond **−0.1
poverty-rate percentage point per +1 GDP-growth percentage point** and
the p cutoff. Symmetric positive magnitude with the p cutoff is `REFUTED`.
Another estimable result is `PARTIAL`; any source, rank, sample, exposure,
or uncertainty gate failure is `INCONCLUSIVE`. These labels speak only to
the frozen descriptive relation. Every verdict has **zero causal, policy,
school-score, and featured credit** and no position/school mapping.

## Prior work and limitations

Direct scan of all authored hypothesis YAML found three prior records
mentioning Eurostat `ilc_iw01`: bargaining coverage and low-wage poverty,
France RSA/prime d'activité, and eurozone austerity distributional
incidence. None gives the exact WDI GDP-growth → `EMP`/`SAL` forward-rate-
change test. Other growth-poverty and income-distribution cases are
thematically related. The local Bonferroni rule cannot correct this broader
archive selection.

An economy can grow without lowering a *relative* poverty rate. Changes
in wage dispersion, household composition, taxes/transfers, migration,
survey practice, and crisis exposure can confound or reverse the
association. Country and year fixed effects and a survey-year lag do not
identify a causal macroeconomic effect. Cell-level quality flags are
unavailable in the pinned Parquet. Both outcome groups overlap because
employees are part of the employed population.

## Required chronology

1. Commit this document, two YAML specs, two steelmen, key-only roster, and
   guarded runner together. That commit has no measured result artifact.
2. Confirm the two SHA-pinned raw files and exact manifest entries, generate
   a narrow source-lock JSON with `--write-source-lock`, and commit it in a
   separate descendant commit. It must still have no measured results.
3. Only then invoke `--run` to read Eurostat values and missingness. Commit
   every result, including failed or null tests. Run `--verify` to replay
   exact artifacts before public index regeneration.
