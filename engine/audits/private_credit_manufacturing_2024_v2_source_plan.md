# Private credit and manufacturing share, 2024 continuation — frozen plan

The legacy `cross_school_private_credit_manufacturing_financialisation_1990_2023`
run is archived because its hypothesis and result were committed together. Its
known 1990–2023 coefficient is not independent evidence for this test. This
new ID asks a narrower question: among the **181 countries fixed by that old
specification**, is 2022 private-credit depth associated with the subsequent
2022–2024 change in manufacturing value-added share? This is a retrospective
descriptive calibration. The May 2026 source vintage already existed when this
plan was written; no claim of a newly collected or external holdout is made.

## Freeze before selected 2024 outcome access

- `x = WDI FS.AST.PRVT.GD.ZS` in 2022, divided by 10; one unit is ten
  percentage points of GDP.
- `y = WDI NV.IND.MANF.ZS` in 2024 minus its 2022 value, in GDP-share
  percentage points.
- Controls: 2022 manufacturing share and the natural log of 2022 WDI real
  GDP per capita (`NY.GDP.PCAP.KD`). An intercept is included.
- Estimator: ordinary least squares with HC3 heteroskedasticity-robust
  covariance. No country weighting, imputation, winsorisation, regional
  selection, alternate year, or covariate substitution.
- Eligibility: each of the four selected source cells must be finite;
  GDP per capita must be positive; credit and manufacturing shares must be
  nonnegative and at most 300 and 100, respectively. WDI `obs_status` must be
  blank for each cell. Exactly one row per country-year-indicator is required.
- Minimum complete sample: 80 countries. Credit depth IQR must be at least 10
  percentage points of GDP; the four-column design matrix must have full
  rank; the HC3 standard error and confidence interval must be finite.
  Any failure yields `INCONCLUSIVE` before a directional verdict.
- `SUPPORTED` requires beta <= -0.10 manufacturing-share points per ten
  credit/GDP points and a two-sided 95% HC3 confidence interval entirely
  below zero. `REFUTED` requires beta >= +0.10 and its interval entirely
  above zero. All other valid estimates are `PARTIAL`.
- One test, one outcome, no secondary directional verdict. The test is
  associational; zero causal, school, policy, or featured score credit.

Source files and hashes are pinned in the hypothesis and runner. The World
Bank WDI fetch manifest is `data/manifests/fetch_run_2026-05-05T200056Z.yaml`
with SHA-256 `a571d660fd359d245176b77e595b59923a90a1e40a799ea56c13f001a7b09945`.
The old full-source reader filtered its fitted panel to 2023 or earlier; its
aggregate old coefficient was already known. No selected 2024 WDI values or
null masks were opened while constructing this registration.

Execution order: commit this plan, new hypothesis, steelman, and runner;
then derive a key-only source lock and commit it separately; then allow the
runner to read selected numeric source columns and write the result. The
runner must verify immutable registration, source hashes, source lock and
exact replay. Keep the old record and verdict unchanged.
