# OECD tertiary migrant/native employment gap × EPL: preregistration

Registered before either selected OECD `value` column or its value-null pattern
was opened for this study. Only source metadata, hashes, categorical dimensions,
country/year keys, and the archived hypothesis text were inspected. The study
is a **descriptive country-panel calibration** with zero policy, school,
causal, and featured credit.

## Source and sample contract

- Outcome: OECD International Migration Database SDMX
  `OECD.ELS.IMD,DSD_MIG@DF_MIG_EMP_EDU,1.0`, parquet
  `data/vintages/oecd/OECD.ELS.IMD_DSD_MIG_DF_MIG_EMP_EDU_1.0@2026-07-23T150450Z.parquet`,
  SHA-256 `96b522cb77e78684c050d96efb7412489773b735243d6ada537e757817c25536`,
  committed fetch manifest `data/manifests/fetch_run_2026-07-23T150922Z.yaml`.
  Select `CITIZENSHIP=_Z`, `FREQ=A`, `MEASURE=EMP_WAP`, `SEX=_T`,
  `EDUCATION_LEV=ISCED11_5T8`, `UNIT_MEASURE=PT_POP_SUB`, and each of
  `BIRTH_PLACE=FB` and `NB`. These are **employment rates in percentage
  points**, not migrant stocks, flows, or tertiary-attainment shares. No
  selected dimension-key duplicates were found.
- Treatment: OECD Employment Protection Legislation official workbook,
  recorded as `OECD.ELS.EMP,DSD_EPL_OV@DF_EPL_OV,1.0`, parquet
  `data/vintages/oecd/OECD.ELS.EMP_DSD_EPL_OV_DF_EPL_OV_1.0@2026-07-23T154113Z.parquet`,
  SHA-256 `8a25f91e01153564e8db18723e69ed41298c339255a6ac41b67942dc86022fcd`,
  committed fetch manifest `data/manifests/fetch_run_2026-07-23T154936Z.yaml`.
  Use only `indicator=EPR_V1`, the 0–6 regular-worker summary index, higher
  meaning stricter protection. The manifest records an official OECD XLSX
  fallback because its SDMX endpoint returned 404. One row per source
  country-year; no duplicates.
- The explicitly frozen source-name-to-ISO3 mapping is
  `data/pinned_evidence/oecd_migrant_epl_crosswalk_2026.csv`, SHA-256
  `9bc900291ab4ecb0764397964ff4c762b6dfa03adb640c491a136f0c0b1253f3`.
  It contains 35 intersecting national names; non-country EU aggregates are
  excluded. Chile, Colombia, Costa Rica, and Türkiye have fewer than three
  eligible key years and are excluded without inspecting measured values.
- Candidate t is 2015–2023. For each country-year require both birth-place
  slices at t and t+1, plus EPL at t-1 and t. Keep countries with at least
  three such key-only t years. The exact sorted 265-row / 31-country roster
  is `data/pinned_evidence/oecd_migrant_epl_key_roster_2026.csv`, SHA-256
  `ac9afc86da547c01e9dc11b73e628f5d147e1be4ef7636196f0fb253ad43b8e5`.
  It is serialized as `country_iso3,year\n` plus one UTF-8 LF per row,
  sorted by `(year,country_iso3)`. These are key-only upper bounds; numeric
  availability and variation have not been inspected.

## Estimand, inference, and decision gate

Define `Gap(c,y) = employment_rate_NB(c,y) - employment_rate_FB(c,y)` in
percentage points, `Y(c,t) = Gap(c,t+1) - Gap(c,t)`, and
`X(c,t) = EPR_V1(c,t) - EPR_V1(c,t-1)`. Fit one OLS specification:

`Y(c,t) = alpha_c + lambda_t + beta*X(c,t) + error(c,t)`.

Country and t-year effects are categorical. Use country-cluster CR1
correction `G/(G-1) * (N-1)/(N-K)` and a two-sided Student-t test with
`G-1` degrees of freedom. The sole primary coefficient is `beta`, in
percentage points of **next-year gap change per one full EPL index point**.
No automatic covariate selection, imputation, alternate lag, country group,
or endpoint is allowed after values are opened.

After the separate committed source lock, selected employment rates must be
finite and in `[0,100]`, and EPL values finite and in `[0,6]`. Drop only
roster rows lacking all six valid selected values (FB/NB at t and t+1,
EPL at t-1 and t); do not select countries by observed effects. Then remove
countries with fewer than three remaining rows. Require at least **200
valid country-years in 25 countries** and at least **20 country-years across
10 countries** with `|X| >= 0.05` EPL index point. Also require a full-rank
fixed-effect design and finite positive clustered standard error. Any floor
failure is **INCONCLUSIVE**.

For an estimable panel, a positive `beta >= 1.0` and two-sided `p <= 0.005`
is **SUPPORTED** as a directional descriptive association; a negative
`beta <= -1.0` at the same cutoff is **REFUTED**. Everything else is
**PARTIAL**. This p cutoff is a conservative local screen, not a global
multiplicity correction for the visible research archive. As a prespecified
**diagnostic only**, rerun the same model after omitting t=2019–2021 (whose
forward windows include the pandemic). This diagnostic cannot alter the
primary verdict.

## Prior-overlap and interpretation limits

The archived `demo_australia_high_skill_migration` uses a foreign/native
employment gap to discuss Australian skill-stream selection. The archived
Canada points-system and migration wage-skill specs cite the same OECD
`MIG_EMP_EDU` dataflow as if it measured tertiary attainment or migrant
share, although the source dimension label is `Employment rate`. Many EPL
specs test aggregate, youth, or low-education unemployment, not this
foreign/native tertiary gap. Therefore this pairing is distinct in measured
question and source semantics, but it is **not independent confirmation** of
the visible research programme.

EPL is a general labour regulation, not migration policy. Its changes may
respond to labour conditions, while the foreign-born tertiary group can
change composition and differ in sector exposure. Country/year effects and
one-year ordering do not identify a causal effect. Preserve an inconclusive,
null, adverse, or sensitive result exactly as observed. No policy, school,
causal, or featured credit follows from this test.
