# Result card - wdi_tertiary_attainment_labor_productivity_2000_2023

**Verdict:** supported - 17 of 21 countries passed (81.0%); median labor_productivity_growth_pct = 43.78

## Predeclared Threshold

SUPPORTED if n>=15, at least 70% of large-tertiary-gain countries increase output per worker by >=20%, and the median gain is >=25%. REFUTED if fewer than 50% pass or the median gain is <5%. Otherwise PARTIAL.

Threshold expression: `n >= 15 AND pass_rate >= 0.70 AND median_labor_productivity_growth_pct >= 25`

## Metrics

- n_countries: 21
- countries_passing: 17
- pass_rate: 0.8095238095238095
- median_labor_productivity_growth_pct: 43.77821269416413

## Country Panel

| country_iso3 | country_name | tertiary_attainment_gain_pp | labor_productivity_growth_pct | pass |
|---|---|---|---|---|
| ALB | Albania | 10.08 | 129.13 | yes |
| AUS | Australia | 15.86 | 19.49 | no |
| BOL | Bolivia | 12.10 | 23.83 | yes |
| CAN | Canada | 15.14 | 11.55 | no |
| CRI | Costa Rica | 11.16 | 69.71 | yes |
| CZE | Czechia | 21.11 | 49.89 | yes |
| IRL | Ireland | 11.09 | 106.08 | yes |
| IRN | Iran, Islamic Rep. | 11.83 | 28.80 | yes |
| KOR | Korea, Rep. | 13.65 | 69.24 | yes |
| LTU | Lithuania | 14.92 | 137.73 | yes |
| MKD | North Macedonia | 11.40 | 43.78 | yes |
| MLT | Malta | 13.22 | 34.74 | yes |
| MNG | Mongolia | 18.93 | 160.21 | yes |
| MUS | Mauritius | 10.99 | 66.27 | yes |
| PRT | Portugal | 16.22 | 22.12 | yes |
| PSE | West Bank and Gaza | 14.53 | 15.41 | no |
| SAU | Saudi Arabia | 15.96 | -30.16 | no |
| SGP | Singapore | 18.67 | 64.02 | yes |
| SRB | Serbia | 10.80 | 106.78 | yes |
| SWE | Sweden | 12.84 | 24.97 | yes |
| USA | United States | 12.73 | 36.84 | yes |

## Interpretation

This is a descriptive structural-screen verdict using local WDI/OWID vintages.
It grades the predeclared pattern, not a causal effect of a single policy lever.

## Steelman

See `hypotheses/steelman/wdi_tertiary_attainment_labor_productivity_2000_2023.md`.
