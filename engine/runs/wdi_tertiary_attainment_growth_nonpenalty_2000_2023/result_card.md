# Result card - wdi_tertiary_attainment_growth_nonpenalty_2000_2023

**Verdict:** supported - 17 of 22 countries passed (77.3%); median avg_real_gdp_pc_growth = 2.48

## Predeclared Threshold

SUPPORTED if n>=15, at least 65% of large-tertiary-gain countries average >=1% real GDP-per-capita growth, and the median is >=1%. REFUTED if fewer than 45% pass or the median is <0%. Otherwise PARTIAL.

Threshold expression: `n >= 15 AND pass_rate >= 0.65 AND median_avg_real_gdp_pc_growth >= 1`

## Metrics

- n_countries: 22
- countries_passing: 17
- pass_rate: 0.7727272727272727
- median_avg_real_gdp_pc_growth: 2.480595118864456

## Country Panel

| country_iso3 | country_name | tertiary_attainment_gain_pp | avg_real_gdp_pc_growth | pass |
|---|---|---|---|---|
| ALB | Albania | 10.08 | 5.22 | yes |
| AUS | Australia | 15.86 | 1.36 | yes |
| BOL | Bolivia | 12.10 | 1.95 | yes |
| CAN | Canada | 15.14 | 0.92 | no |
| CRI | Costa Rica | 11.16 | 2.71 | yes |
| CZE | Czechia | 21.11 | 2.25 | yes |
| IRL | Ireland | 11.09 | 3.84 | yes |
| IRN | Iran, Islamic Rep. | 11.83 | 1.84 | yes |
| KOR | Korea, Rep. | 13.65 | 3.39 | yes |
| LTU | Lithuania | 14.92 | 4.88 | yes |
| MKD | North Macedonia | 11.40 | 3.04 | yes |
| MLT | Malta | 13.22 | 3.67 | yes |
| MNG | Mongolia | 18.93 | 4.46 | yes |
| MUS | Mauritius | 10.99 | 3.26 | yes |
| PRT | Portugal | 16.22 | 0.90 | no |
| PSE | West Bank and Gaza | 14.53 | 0.54 | no |
| SAU | Saudi Arabia | 15.96 | 0.69 | no |
| SGP | Singapore | 18.67 | 3.10 | yes |
| SRB | Serbia | 10.80 | 3.88 | yes |
| SWE | Sweden | 12.84 | 1.30 | yes |
| USA | United States | 12.73 | 1.39 | yes |
| VEN | Venezuela, RB | 10.87 | -3.17 | no |

## Interpretation

This is a descriptive structural-screen verdict using local WDI/OWID vintages.
It grades the predeclared pattern, not a causal effect of a single policy lever.

## Steelman

See `hypotheses/steelman/wdi_tertiary_attainment_growth_nonpenalty_2000_2023.md`.
