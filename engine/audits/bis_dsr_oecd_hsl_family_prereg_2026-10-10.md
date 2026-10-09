# BIS household DSR × OECD How's Life: prospective four-test family

Registered before reading selected OECD How's Life (HSL) `value` cells or their
null patterns. The preflight inspected only source schemas, categorical measure
labels, country/year keys, raw hashes, the BIS **exposure** values needed to set
an identification floor, and the visible hypothesis archive. This is a
**descriptive calibration**, with zero school, policy, causal, and featured
credit. The pre-existing archive was visible, so the local correction below
must not be described as archive-wide multiplicity control.

## Custody and measurement

- BIS treatment: official BIS `WS_DSR` quarterly debt service ratios, pinned
  parquet `data/vintages/bis/WS_DSR@2026-07-22T141212Z.parquet`, raw SHA-256
  `59cb6b2f260d3132f826a15ccf585a3016af8516c4d0c2197a5fda2c2916b3fd`.
  Source entry is in committed `data/manifests/fetch_run_2026-07-22T141212Z.yaml`,
  manifest SHA-256 `895761a2da3bd2554da4466becd7fa85837258ce80442c519362bb9d4c5eaea2`.
  Select `FREQ=Q`, `DSR_BORROWERS=H`, and `UNIT_MEASURE=367`; `H` covers
  households and nonprofit institutions serving households. BIS DSR measures
  principal plus interest payments relative to income. The H-sector country
  overlap here covers 17 economies; BIS cautions that changes within an
  economy are more interpretable than DSR levels across economies because
  estimation assumptions differ. Official overview:
  <https://data.bis.org/topics/DSR?m=6_380_671>. Require exact Q1-Q4
  keys in each calendar year, with no quarterly duplication. For each year,
  take the arithmetic mean of four quarterly percentage ratios. Exposure
  `X(c,t) = mean_DSR(c,t) - mean_DSR(c,t-1)`, in percentage points.
- OECD outcome: the raw filename
  `data/vintages/oecd/OECD.ELS.HD_DSD_HH_DASH_DF_HSG_INEQ_1.0@2026-07-23T150432Z.parquet`
  is a historical alias; the committed manifest's actual `source_url` is the
  OECD WISE How's Life current well-being feed
  `OECD.WISE.WDP,DSD_HSL@DF_HSL_CWB,1.1`, not a housing-only feed. Raw SHA-256
  `ac7581cb015748d97a21d4feadd08a3afb16cb1d5912af9e0997913ce4db65db`;
  committed `data/manifests/fetch_run_2026-07-23T150922Z.yaml` SHA-256
  `f8d2a682717c02832a2cf323fb5ea777139502e14987348859f3114042bece51`.
  The source is a 2026-07-23 fetch of the OECD HSL feed. The OECD *How's Life?
  2024* reader guide and well-being definitions explain the indicators; do
  not assume the locally fetched data are frozen as a 2024 publication table.
  Official definitions:
  <https://www.oecd.org/en/publications/how-s-life-2024_90ba854a-en/full-report/component-3.html>
  and <https://www.oecd.org/wise/oecd-well-being-database-definitions.pdf>.
- Pin `AGE=_T`, `SEX=_T`, and `EDUCATION_LEV=_T` for all four outcomes. Exact
  measure and unit labels from source categorical columns:

  | Case | `MEASURE` | Source label | `UNIT_MEASURE` | Adverse orientation |
  | --- | --- | --- | --- | --- |
  | `ends_meet` | `1_5` | Difficulty making ends meet | `PT_POP_Y_GE16`, percent of people age 16+ | `+` |
  | `housing_affordability` | `3_2` | Housing affordability | `PT_B7G_S14`, percent of household gross adjusted disposable income | `-` |
  | `home_warmth` | `3_5` | Inability to keep home adequately warm | `PT_POP_Y_GE16`, percent of people age 16+ | `+` |
  | `negative_affect` | `11_2` | Negative affect balance | `PT_POP_Y_GE15`, percent of people age 15+ | `+` |

  `3_2` means **income remaining after housing rents and maintenance**;
  higher is better. It is not the distinct `3_3` housing-cost-overburden rate.
  `11_2` uses Gallup World Poll subjective responses; OECD reporting can pool
  three-year country averages, so adjacent changes may be overlapping and
  must not be presented as independent annual survey shocks. The two
  EU-heavy household-hardship endpoints are likely based on EU-SILC. We do
  not treat a country-year key as proof of a nonmissing, independent outcome.

The two whole fetch manifests contain unrelated absolute home paths. They
remain referenced by exact SHA only; the later tracked source lock must
extract only the two selected entries, their original manifest hashes, raw
SHAs, and the key-only roster. Never copy the whole manifests into an
external report or result packet.

## Frozen sample and test

The key-only roster is
`data/pinned_evidence/bis_dsr_oecd_hsl_family_2026_key_roster.csv`, SHA-256
`ecd0847a9dc555cc4272e4771b33db3b435f5b5e7a87c3a0383d19747b11a997`.
It is UTF-8 CSV `case_id,country_iso3,year\n`, sorted by case in the order
below, then treatment year and ISO3. BIS country code to ISO3 mapping is
frozen in `scripts/run_bis_dsr_oecd_hsl_2026.py`. All four exact HSL
country-year selections had zero duplicate keys. Candidate `t` requires HSL
at `t` and `t+1`, and all four BIS quarters at `t-1` and `t`; countries need
at least three key-only candidate years. The roster is an upper bound only.

| Case | `t` years | Key-only rows/countries | Pre-read `|X| >= 0.1` exposure rows/countries | Minimum measured rows/countries | Minimum measured material-exposure rows/countries |
| --- | --- | ---: | ---: | ---: | ---: |
| `ends_meet` | 2004-2024 | 242 / 12 | 184 / 12 | 180 / 10 | 120 / 10 |
| `housing_affordability` | 2004-2024 | 340 / 17 | 254 / 17 | 260 / 14 | 170 / 14 |
| `home_warmth` | 2004-2024 | 240 / 12 | 183 / 12 | 180 / 10 | 120 / 10 |
| `negative_affect` | 2006-2024 | 323 / 17 | 239 / 17 | 240 / 14 | 160 / 14 |

After the separate committed source lock, require finite treatment and
outcome values within `[0,100]` at every selected quarter and outcome year.
Drop only incomplete/out-of-range roster pairs, then countries with fewer
than three complete pairs. Do not impute, replace sources, select on observed
signs, filter by outcome status after inspection, or choose a later time
window. Record the selected OECD observation statuses as diagnostics without
using them to change the sample or verdict.

Let `Z(c,y)` be the exact HSL measure, and let `s` be the orientation above.
`Y(c,t)=s * [Z(c,t+1)-Z(c,t)]`. Fit exactly one primary OLS model per case:

`Y(c,t) = alpha_c + lambda_t + beta X(c,t) + error(c,t)`.

Use categorical country and treatment-year effects, country-clustered CR1
small-sample correction, and a two-sided Student t distribution with `G-1`
degrees of freedom. Require a full-rank design and finite positive cluster
standard error. There are no fitted covariates, outcome switches, alternate
lags, or post-result exclusion diagnostics in the decision rule.

All four cases form **one Bonferroni family at family alpha 0.01**: each has
two-sided `p <= 0.0025`, even if another test is inconclusive. For each case,
**INCONCLUSIVE** if its source, roster, sample, meaningful exposure, design,
or uncertainty gate fails. Otherwise, **SUPPORTED** only if adverse-oriented
`beta >= +0.25` outcome percentage point per one DSR percentage point and
`p <= 0.0025`; **REFUTED** only if `beta <= -0.25` and the same p cutoff;
otherwise **PARTIAL**. These labels describe this measured association only.

## Prior archive and limits

The visible BIS archive tests household DSR against consumption, housing
prices, credit, unemployment and other macro outcomes. OECD HSL housing-cost
overburden has been used with housing public spending, construction, and
consumption questions. No exact DSR-change to these four HSL-change pairings
was found in the registered hypothesis text. Their source, measured outcome,
and timing are distinct, but shared countries and upstream macro shocks mean
this is not an independent holdout against the wider IESET search.

Debt-service burden is neither a randomized treatment nor an observed policy.
Interest-rate changes, indebtedness, income, housing markets, energy prices,
and survey composition can jointly move exposure and outcomes. The
particularly subjective `negative_affect` endpoint has survey sampling and
pooling limits. Preserve negative, null, missing, and inconclusive results.
Neither a positive result nor a refutation awards causal, policy, school, or
featured credit.
