# Result card — property_rights_long_run_income_frontier

**Verdict:** partial — TWFE β_RL=+0.0048 (SE 0.0044, p=0.277, n=2474), R²=0.466. Does not meet falsification threshold.

## Design

Broad panel 1996-2018. Outcome: 5-year-forward annualised log GDP-per-capita
growth (Maddison). Treatment: WGI Rule of Law (`GOV_WGI_RL.EST`) as property-rights proxy.
Controls: log initial GDP per capita. Estimator: TWFE (country + year fixed effects),
clustered SE by country.

## Threshold

SUPPORTED if β_RL > 0 and p < 0.05.
REFUTED if β_RL < 0 and p < 0.05.
Otherwise PARTIAL.

## Metrics

| Metric | Value |
|---|---|
| Observations | 2474 |
| Countries | 165 |
| β_RL | +0.0048 |
| SE | 0.0044 |
| 95% CI | [-0.0039, +0.0135] |
| p-value | 0.277 |
| R² within | 0.466 |

## Limitations

- WGI Rule of Law is perception-based and includes dimensions beyond narrow
  property-rights security (e.g., contract enforcement, judicial independence).
- No direct control for state investment share as specified in the original hypothesis.
- 5-year-forward windows shrink sample at panel ends.
- TWFE with heterogeneous effects may be biased.

## Next robustness checks

- Control for WGI Government Effectiveness (state-capacity proxy).
- Use PWT instead of Maddison for GDP pc.
- Test with 10-year-forward growth windows.
- Add human-capital controls where available.
