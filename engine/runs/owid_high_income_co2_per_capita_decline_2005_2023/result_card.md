# Result card - owid_high_income_co2_per_capita_decline_2005_2023

**Verdict:** supported - 19 of 20 high-income economies passed; median per-capita CO2 change -39.2%

## Predeclared Threshold

SUPPORTED if at least 75% of the high-income panel reduces per-capita CO2 by >=15% and the median decline is >=25%. REFUTED if fewer than 50% pass or median decline is less than 10%. Otherwise PARTIAL.

Threshold expression: `n >= 18 AND pass_rate >= 0.75 AND median_co2_per_capita_pct_change <= -25`

## Metrics

- n_countries: 20
- pass_rate: 0.95
- median_co2_per_capita_pct_change: -39.21568926139226

## Country Endpoints

| country_iso3 | country_name | start_year | end_year | co2_per_capita_pct_change | pass |
|---|---|---|---|---|---|
| AUS | Australia | 2005 | 2023 | -23.43 | yes |
| AUT | Austria | 2005 | 2023 | -35.15 | yes |
| BEL | Belgium | 2005 | 2023 | -39.69 | yes |
| CAN | Canada | 2005 | 2023 | -21.06 | yes |
| CHE | Switzerland | 2005 | 2023 | -41.47 | yes |
| DEU | Germany | 2005 | 2023 | -33.61 | yes |
| DNK | Denmark | 2005 | 2023 | -49.03 | yes |
| ESP | Spain | 2005 | 2023 | -46.20 | yes |
| FIN | Finland | 2005 | 2023 | -47.81 | yes |
| FRA | France | 2005 | 2023 | -39.79 | yes |
| GBR | United Kingdom | 2005 | 2023 | -52.38 | yes |
| IRL | Ireland | 2005 | 2023 | -44.26 | yes |
| ITA | Italy | 2005 | 2023 | -38.74 | yes |
| JPN | Japan | 2005 | 2023 | -21.10 | yes |
| KOR | South Korea | 2005 | 2023 | 9.25 | no |
| NLD | Netherlands | 2005 | 2023 | -40.22 | yes |
| NOR | Norway | 2005 | 2023 | -24.77 | yes |
| NZL | New Zealand | 2005 | 2023 | -32.55 | yes |
| SWE | Sweden | 2005 | 2023 | -41.60 | yes |
| USA | United States | 2005 | 2023 | -30.89 | yes |

## Interpretation

This is a descriptive endpoint-panel test using local OWID vintages. It grades the
predeclared pattern only; it does not identify a policy-level causal effect.
