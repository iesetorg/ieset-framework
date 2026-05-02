# Result card — catch_up_growth_fades_after_middle_income_threshold

**Verdict:** partial — Diff +0.38pp below threshold (1pp) or not significant (p=0.000).

## Design

PWT panel 1960-2019. 5-year-forward annualised log GDP-per-capita growth
(RGDPE/pop). Split by income relative to US frontier in the base year of each growth
window (< 40% vs ≥ 40%).

## Threshold

SUPPORTED if mean growth below-threshold ≥ mean growth above-threshold + 1pp/yr
AND significant at p < 0.05. REFUTED if below-threshold growth ≤ above-threshold growth.
Otherwise PARTIAL.

## Metrics

| Metric | Value |
|---|---|
| Country-year observations | 8819 |
| Countries | 183 |
| Below-40% observations | 6490 |
| Above-40% observations | 2329 |
| Mean growth below | +2.38%/yr |
| Mean growth above | +2.00%/yr |
| Difference | +0.38pp/yr |
| t-statistic | 3.65 |
| p-value | 0.000 |
| Spline at 40% coef | -2.34pp |
| Spline p-value | 0.000 |

## Robustness

Linear spline regression: growth = β0 + β1·rel_us + β2·max(0, rel_us − 0.40).
β2 = -2.34pp (p=0.000). Positive β2 would mean growth is *higher* above the
threshold after controlling for level; negative β2 supports fading catch-up.

## Limitations

- Cross-country comparison, not within-country crossing of the threshold.
- 5-year-forward windows shrink sample at panel ends.
- Relative-to-US threshold conflates domestic growth with US slowdowns.
- No controls for initial human capital, institutions, or commodity cycles.

## Next robustness checks

- Use 10-year-forward growth windows.
- Control for country fixed effects (within-estimator).
- Test alternative thresholds (30%, 50% of US).
- Use Maddison instead of PWT for longer historical coverage.
