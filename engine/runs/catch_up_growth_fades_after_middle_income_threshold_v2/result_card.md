# Result card — catch_up_growth_fades_after_middle_income_threshold_v2

**Verdict:** partial — Diff +0.11pp below threshold (1pp) or not significant (p=0.166).

## Design

Maddison panel 1960-2018. 10-year-forward annualised log GDP-per-capita growth.
Split by income relative to US frontier (< 40% vs ≥ 40%).

## Methodology Note

This is a v2 robustness check for `catch_up_growth_fades_after_middle_income_threshold`.
v1 used PWT RGDPE + 5-year-forward growth and found PARTIAL (+0.38pp diff, p<0.001).
v2 uses Maddison (longer coverage, different PPP base) + 10-year windows to test
sensitivity to data source and growth horizon.

## Metrics

| Metric | Value |
|---|---|
| Observations | 7948 |
| Countries | 169 |
| Mean growth below | +2.08%/yr |
| Mean growth above | +1.97%/yr |
| Difference | +0.11pp/yr |
| p-value | 0.166 |
| Spline coef | -3.34pp |

## Interpretation

See v1 result card for primary interpretation. This v2 tests whether the
partial verdict is sensitive to data source (Maddison vs PWT) and growth
horizon (10-year vs 5-year).
