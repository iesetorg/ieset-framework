# Result card — property_rights_long_run_income_frontier_v2

**Verdict:** partial — Cross-section β_RL=-0.0028 (SE 0.0043, p=0.506, n=165), R²=0.016.

## Design

Cross-section of 165 countries, 1996-2018. Outcome: mean annual
log GDP-per-capita growth (Maddison). Treatment: mean WGI Rule of Law.
Control: log initial GDP per capita. Estimator: OLS with HC3 SEs.

## Methodology Note

This is a v2 robustness check for `property_rights_long_run_income_frontier`.
v1 used TWFE panel with 5-year-forward growth and found PARTIAL (β=+0.0048, p=0.277).
v2 uses a country-mean cross-section to test whether the panel result is driven
by within-country vs between-country variation.

## Metrics

| Metric | Value |
|---|---|
| Countries | 165 |
| β_RL | -0.0028 |
| SE | 0.0043 |
| 95% CI | [-0.0112, +0.0055] |
| p-value | 0.506 |
| R² | 0.016 |

## Interpretation

See v1 result card for primary interpretation. This v2 tests whether the
partial TWFE panel result reflects weak between-country association.
