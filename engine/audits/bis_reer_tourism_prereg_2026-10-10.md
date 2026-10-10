# BIS real appreciation and international tourist arrivals: blind preregistration

## Question and prior evidence

One fixed descriptive test asks whether a year with at least five log points
of broad real EER appreciation predicts lower *next-year growth* in inbound
tourist-arrival trips across 62 fixed economies, 2004-2018. Earlier IESET
REER/export results, country-specific tourism cases, and a tourism-as-exposure
employment test were visible before this design. Their estimates are not
independent validation for this pair. An exact BIS WS_EER-to-WDI ST.INT.ARVL
treatment/outcome pair was absent from the registered corpus when checked.
The prior confidence is 0.35, reflecting the tourism-origin mismatch in the
BIS manufacturing-trade basket and many omitted travel shocks.

## Blindness and selection record

Before this registration, only BIS treatment values and statuses, WDI GDP-growth
control values, and WDI tourism schema/country/year/indicator keys were read.
No tourism value, null mask, observation-status field, selected outcome trend,
coefficient, or outcome-derived completeness count was opened or calculated.
The WDI file includes a rectangular country/year key grid, so its 930
country-year upper bound is **not** a measured coverage count. Whole-file
SHA-256 hashing checks custody without decoding candidate outcome values.

The exposure threshold and period were selected after treatment-only
screening. Continuous REER changes in 2000-2018 had concentration in early
2000s crisis economies; the 2004 start removes those early years, and the
five-log-point event is broadly dispersed. The 2018 endpoint makes t+1=2019,
before COVID-19. These choices are adaptive to treatment data, not independent
randomization. No tourism outcome data influenced them.

With exactly twelve valid monthly BIS observations per year, the treatment and
GDP-control plus outcome-**key** envelope has 930 candidate rows in 62
countries for t=2004-2018. The fixed event rule marks 118 rows in 40
countries. After GDP growth and country/year effects, the treatment-only event
residual sum of squares has maximum country share 4.1%, top-three share
11.6%, and top-one-percent-row share 10.6%. These diagnostics are not
outcome-complete diagnostics; the runner will recompute its stronger frozen
post-complete-case concentration gate after the source lock.

## Fixed estimator and decisions

Let R_ct be the arithmetic mean of the twelve BIS monthly index values in year
t. Exposure is 1[100 log(R_ct/R_c,t-1) >= 5] and zero otherwise. The outcome is
log(A_c,t+1) - log(A_ct), requiring positive finite WDI arrival counts at both
endpoints. Estimate one OLS coefficient on exposure, adjusting for log(A_ct),
WDI real GDP growth at t, country effects, and treatment-year effects.
Use country-cluster CR1 standard errors and a two-sided Student t reference
with G-1 degrees of freedom. There are no trims, imputed values, alternative
lags, or post-result specification choices.

If fewer than 400 complete pairs, 25 countries, five complete years per
retained country, 30 events, or 15 event countries remain, label
INCONCLUSIVE. Likewise if residualized exposure has >15% of sum of
squares in one country, >20% in the top 1% of rows, rank deficiency, or
nonfinite clustered uncertainty. Otherwise SUPPORT requires beta <= -0.03
log points and two-sided p <= 0.01; REFUTE requires beta >= +0.03 and
p <= 0.01. Every other estimable outcome is PARTIAL. This one-test family
uses alpha 0.01; it does not correct earlier corpus-wide adaptive searching.

## Frozen source custody and sequence

The key roster is `data/pinned_evidence/reer_tourism_2026_key_roster.csv`,
SHA-256 `0dc4d0162c1dcdc289f904c9331da8e08f4f2a98e8e57b3163c2a396771146eb`.
Country names are explicit ISO3 codes; XM and WDI aggregate keys are excluded.
The scope vocabulary gains \`tourism_activity\` for inbound visitor volume,
which avoids misclassifying the outcome as trade liberalization.

| Role | Pinned raw SHA-256 | Fetch manifest SHA-256 |
| --- | --- | --- |
| BIS monthly broad real EER, WS_EER | `57bbce3e22fc428c8cd8ddee8a998d273b5240a816af89e532b81d41ade35170` | `1768f0d7c38c93f1ad4df591b0b1634b3460faa964f6267874b8798b7b8dbb81` |
| WDI international arrivals, ST.INT.ARVL | `1336df1cce2b3a2e784f917caa9487753d4cf53ad4ec65e5ea2fb045b0d41da5` | `5022cf82e5656d89c54d3c0df1cc3c12718b93896488eebfde3ffa197beef112` |
| WDI real GDP growth, NY.GDP.MKTP.KD.ZG | `db76a52909929c6cd3ca1dd3d1fdc4b28d28cbaea92e16cb59e88ee53d3f2e58` | `a571d660fd359d245176b77e595b59923a90a1e40a799ea56c13f001a7b09945` |

The narrow source lock must be written and committed **after** the first-addition
commit containing this spec, steelman, audit, roster, runner, and synthetic
tests. The lock carries the preregistration commit, exact hashes, source
metadata, and key preflight, without copying path-bearing whole manifests.
Only after its separate commit may `--run` read tourism values or statuses.
`--verify` must replay the frozen model and compare each result artifact.

The BIS definition is documented at
[BIS effective exchange rates](https://data.bis.org/topics/EER?lang=en);
WDI tourism counting and cross-country reporting limitations are in
[World Bank ST.INT.ARVL metadata](https://databank.worldbank.org/metadataglossary/world-development-indicators/series/ST.INT.ARVL).
This is a descriptive association with zero causal, policy, position,
school-score, and featured credit.
