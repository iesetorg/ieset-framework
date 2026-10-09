# CEPII RTA partner expansion and WITS exported HS6 count: preregistration

Registered before the WITS `value` column or value-null pattern was opened
for this study. The old CEPII FTA-growth/openness verdict was PARTIAL, the
CEPII FTA-market-potential/private-investment holdout was PARTIAL, the
consumer-choice variety proxy screen was REFUTED, and related WITS export
count as a control and import-variety hypotheses were already registered.
The new measured outcome and conditional estimand are distinct, but the
mechanism and sources are not independent of this visible search history.

## Fixed source and key contract

- CEPII `fta_accession_indicator@2026-05-15T172455Z.parquet`, SHA-256
  `3125c268836d9e1e66d018d4b7d0acf3a7c918bd9f7fd77c3814109f65c09645`,
  built from Gravity V202211 `fta_wto`. The raw CEPII archive is SHA-256
  `7ffea0510a536587f2f9295bbafef4a312a36b366acc256eb6d9770fe35e44b1`.
- WITS `unique_hs6_products@2026-07-23T153652Z.parquet`, SHA-256
  `29db44b85d263bfc92307182b19f3baf4073dae446e5c3af37d82a284bfb2934`.
  Keep only annual `NMBR-XPRT-HS6-PRDCT`, partner `WLD`, product `999999`,
  series `unique_hs6_products`, one row per reporter-year.
- Use pycountry 24.6.1 current-country alpha-3 codes. Sorted codes with
  one LF after every code hash to
  `cc306b7deb4ff39f16097111f5a48412bc49e268a7fa5dfc42a9c9427adf0e6b`.
  The full selected roster is committed at
  `data/pinned_evidence/cepii_rta_hs6_key_roster_2026.csv`; replay reads that
  file directly and does not depend on pycountry at runtime.
- Candidate event year t is 1993 through 2019 inclusive. Require WITS keys
  for every year t-3 through t+1. CEPII event years are indicator `value=1`
  from 1990 onward. Event role means t is the sole event in the closed
  [t-3,t+1] window. Control role means that window has zero events. Controls
  can have older RTA status or expansions outside this window and are not
  called untreated. All other windows are excluded.
- Serialize `role,country_iso3,year\n` plus one UTF-8 LF row per key, sorted
  by `(year,country_iso3,role)`. The frozen key-only intersection contains
  169 event rows from 105 countries in 24 years and 1,376 control rows from
  153 countries. Combined CSV SHA-256 is
  `57aebe9d5cc9012777b93ed2bd5331313b853857c3913bfaf0850ba963f10ebe`.
  Event-only and control-only hashes are respectively
  `1f41c274a8605425eac89875e4d68a94db935b9ef74d00e8c4f70bf38b73a239`
  and `8a954147e2af8d49fef91a714941bb8e2cbda27eec1560c02368ba93a64ad082`.
- CEPII has 531 adjacent event-year pairs in 79 countries. These do not
  enter an event window unless t is the only event in its closed window.

## Estimand, inference, and gates

Let `L(c,y)=log1p(exported_HS6_product_count(c,y))`. Primary outcome is
`Y(c,t)=L(c,t+1)-L(c,t-1)`. Frozen pre-event trend covariate is
`M(c,t)=L(c,t-1)-L(c,t-3)`, and frozen baseline-level covariate is
`B(c,t)=L(c,t-1)`. Fit

`Y(c,t) = alpha_c + lambda_t + beta*event(c,t) + gamma*M(c,t) + delta*B(c,t) + error(c,t)`.

Country and event-year fixed effects enter as categorical dummies. Use OLS
with no automatic covariate deletion, country-cluster CR1 correction
`G/(G-1) * (N-1)/(N-K)`, and Student-t p values with `G-1` degrees of
freedom, where `G` is the number of country clusters and `K` the full model
matrix rank. The sole primary coefficient is `beta`; two-sided `p<=0.005`
is a conservative local screen, not a claim of global family-wise error
control for already visible tests. A positive or negative point estimate
must additionally reach `abs(beta)>=ln(1.05)=0.04879016416943205` for a
directional label. The baseline level also appears in the change outcome;
this standard change-score adjustment can amplify mean-reversion modeling
choices and is disclosed as a limit.

As a required diagnostic, regress `M(c,t)` on the event flag with the same
country and year effects and CR1 inference; report coefficient, standard
error, two-sided p, and 90% CI, along with role-specific raw means. It is
not a parallel-trends test or a promotion gate. Do not revise the primary
model based on this diagnostic.

Before estimation, require all frozen roster WITS values to be finite,
nonnegative integers; an invalid selected value makes the study
INCONCLUSIVE rather than causing an outcome-dependent drop. Also require
at least 100 event rows in 50 countries, 800 control rows in 80 countries,
and 15 event years; a full-rank design and finite positive clustered
standard error are mandatory. Failing any gate is INCONCLUSIVE.
Otherwise `beta>=ln(1.05)` with `p<=0.005` is SUPPORTED as a descriptive
association; `beta<=-ln(1.05)` with the same cutoff is REFUTED; all other
estimable results are PARTIAL. No policy, causal, school, or featured credit.

There is one registered estimator and one primary endpoint. No alternate
window, country group, lag, transformation, or covariate set may be selected
after values are viewed. Preserve null and adverse results, exact source
pins, provenance, and replay artifacts.
