# Result card - owid_g20_co2_intensity_decline_1990_2022

**Verdict:** supported - 16 of 19 G20 economies passed; median CO2 intensity change -43.2%

## Predeclared Threshold

SUPPORTED if at least 75% of the G20 country panel reduces CO2 intensity by >=25% and the median decline is >=35%. REFUTED if fewer than 50% pass or the median decline is less than 15%. Otherwise PARTIAL.

Threshold expression: `n >= 18 AND pass_rate >= 0.75 AND median_co2_intensity_pct_change <= -35`

## Metrics

- n_countries: 19
- pass_rate: 0.8421052631578947
- median_co2_intensity_pct_change: -43.24565188179379

## Country Endpoints

| country_iso3 | country_name | start_year | end_year | co2_intensity_pct_change | pass |
|---|---|---|---|---|---|
| ARG | Argentina | 1990 | 2022 | -35.09 | yes |
| AUS | Australia | 1990 | 2022 | -52.31 | yes |
| BRA | Brazil | 1990 | 2022 | -18.34 | no |
| CAN | Canada | 1990 | 2022 | -43.25 | yes |
| CHN | China | 1990 | 2022 | -40.80 | yes |
| DEU | Germany | 1990 | 2022 | -67.36 | yes |
| FRA | France | 1990 | 2022 | -54.20 | yes |
| GBR | United Kingdom | 1990 | 2022 | -70.24 | yes |
| IDN | Indonesia | 1990 | 2022 | 0.40 | no |
| IND | India | 1990 | 2022 | -18.13 | no |
| ITA | Italy | 1990 | 2022 | -46.39 | yes |
| JPN | Japan | 1990 | 2022 | -30.91 | yes |
| KOR | South Korea | 1990 | 2022 | -32.59 | yes |
| MEX | Mexico | 1990 | 2022 | -41.97 | yes |
| RUS | Russia | 1990 | 2022 | -67.52 | yes |
| SAU | Saudi Arabia | 1990 | 2022 | -53.73 | yes |
| TUR | Turkey | 1990 | 2022 | -41.45 | yes |
| USA | United States | 1990 | 2022 | -53.25 | yes |
| ZAF | South Africa | 1990 | 2022 | -55.47 | yes |

## Interpretation

This is a descriptive endpoint-panel test using local OWID vintages. It grades the
predeclared pattern only; it does not identify a policy-level causal effect.
