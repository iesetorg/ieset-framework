# Result card — market_reform_without_state_capacity_failure

**Verdict:** refuted — Low-capacity reformers grew +4.26%/yr, at or above high-capacity +3.06%/yr (diff -1.21pp, p=0.037).

## Design

Countries in the top tercile of WGI Regulatory Quality improvement 1996-2016 are
"reformers". Split by 1996 WGI Government Effectiveness median (state-capacity proxy).
Outcome: annualised log GDP-per-capita growth 1996-2019 (PWT).

## Threshold

SUPPORTED if low-capacity reformers' mean growth ≤ high-capacity mean − 1pp/yr
AND significant at p < 0.10.
REFUTED if low-capacity mean growth ≥ high-capacity mean.
Otherwise PARTIAL.

## Metrics

| Metric | Value |
|---|---|
| Reformers (top tercile RQ improvement) | 57 |
| High-capacity reformers | 29 |
| Low-capacity reformers | 28 |
| High-capacity mean growth | +3.06%/yr |
| Low-capacity mean growth | +4.26%/yr |
| Difference | -1.21pp/yr |
| t-statistic | -2.14 |
| p-value | 0.037 |

## Country panel

| ISO3 | ΔRQ 1990-2010 | GE 1990 | High capacity | Growth |
|---:|---:|---:|:---:|:---:|
| AGO | +0.474 | -0.570 | no | +3.26% |
| ALB | +0.854 | -0.970 | no | +4.50% |
| ARE | +0.605 | 0.473 | yes | -1.39% |
| ARM | +1.010 | -0.273 | yes | +6.41% |
| AUS | +0.886 | 1.601 | yes | +1.74% |
| AZE | +1.058 | -1.362 | no | +8.20% |
| BDI | +0.902 | -1.822 | no | +0.34% |
| BGR | +1.075 | -0.603 | no | +3.67% |
| BIH | +1.084 | -1.362 | no | +5.93% |
| CAN | +0.586 | 1.777 | yes | +1.40% |
| CHE | +0.662 | 1.836 | yes | +2.26% |
| CMR | +0.744 | -0.808 | no | +1.43% |
| COD | +0.847 | -1.644 | no | +1.59% |
| COL | +0.573 | -0.053 | yes | +2.20% |
| CZE | +0.481 | 0.659 | yes | +2.53% |
| DEU | +0.534 | 1.778 | yes | +1.97% |
| DOM | +0.495 | -0.303 | yes | +4.30% |
| EST | +0.775 | 0.377 | yes | +5.26% |
| ETH | +0.514 | -1.349 | no | +6.28% |
| FIN | +0.560 | 1.666 | yes | +2.40% |
| GEO | +1.972 | -1.306 | no | +6.97% |
| GMB | +0.564 | -0.586 | no | -0.90% |
| HKG | +0.861 | 1.596 | yes | +2.12% |
| HRV | +0.483 | -0.335 | no | +4.06% |
| IRN | +0.621 | -0.270 | yes | +3.01% |
| IRQ | +1.056 | -1.824 | no | +4.10% |
| ISL | +0.569 | 1.297 | yes | +2.41% |
| ISR | +0.538 | 1.362 | yes | +1.39% |
| JOR | +0.476 | 0.201 | yes | +4.57% |
| JPN | +1.157 | 1.125 | yes | +0.33% |
| KAZ | +0.533 | -1.362 | no | +6.42% |
| KEN | +0.458 | -0.270 | yes | +2.59% |
| KOR | +0.766 | 0.696 | yes | +2.31% |
| LAO | +0.725 | -0.790 | no | +6.69% |
| LBR | +1.542 | -2.028 | no | +7.01% |
| LTU | +0.467 | -0.021 | yes | +5.84% |
| MAC | +1.266 | 0.243 | yes | +4.86% |
| MKD | +0.850 | -0.650 | no | +4.16% |
| MLT | +0.610 | 1.001 | yes | +4.35% |
| MMR | +0.953 | -1.349 | no | +7.13% |
| MNG | +0.470 | -0.586 | no | +6.95% |
| MUS | +0.908 | 0.473 | yes | +1.74% |
| NER | +0.916 | -1.307 | no | +0.40% |
| OMN | +0.857 | 0.268 | yes | +3.84% |
| POL | +0.498 | 0.695 | yes | +4.32% |
| PRY | +0.486 | -0.821 | no | +3.47% |
| PSE | +1.094 | -1.306 | no | +2.80% |
| QAT | +1.140 | 0.235 | yes | +6.01% |
| ROU | +0.870 | -0.874 | no | +5.36% |
| RWA | +1.747 | -1.306 | no | +4.50% |
| SAU | +0.550 | -0.303 | yes | +4.29% |
| SLE | +0.944 | -1.644 | no | +0.73% |
| SRB | +1.420 | -0.541 | no | +4.99% |
| SVK | +0.759 | 0.497 | yes | +3.16% |
| SWE | +0.608 | 1.758 | yes | +2.40% |
| TJK | +0.888 | -1.306 | no | +3.05% |
| VNM | +0.500 | -0.565 | no | +6.21% |

## Limitations

- WGI RQ improvement is an imperfect proxy for market-reform intensity.
- 1990 WGI coverage is thinner than post-1996; some country scores are interpolated.
- GE is a perception-based state-capacity proxy, not a direct administrative-capacity measure.
- Reform episode is defined over a fixed 20-year window; alternative dating may yield
  different reformer sets.

## Next robustness checks

- Use V-Dem liberal-component increase as alternative reform proxy.
- Vary the reform window (1995-2015, 2000-2010).
- Use objective reform indicators (trade liberalisation, privatisation events) where available.
- Control for initial income level and commodity dependence.
