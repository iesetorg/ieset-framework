# Result card - wdi_remittance_consumption_resilience_2009_2021

**Verdict:** supported - 21 of 31 countries passed (67.7%); median avg_private_consumption_growth_shock_years = 2.23

## Predeclared Threshold

SUPPORTED if n>=25, at least 60% of high-remittance economies have non-negative average private-consumption growth in shock years, and the median shock-year average is >=1%. REFUTED if fewer than 45% pass or the median is below -1%. Otherwise PARTIAL.

Threshold expression: `n >= 25 AND pass_rate >= 0.60 AND median_avg_private_consumption_growth_shock_years >= 1`

## Metrics

- n_countries: 31
- countries_passing: 21
- pass_rate: 0.6774193548387096
- median_avg_private_consumption_growth_shock_years: 2.2284411502849033

## Country Panel

| country_iso3 | country_name | avg_remittances_pct_gdp | avg_private_consumption_growth_shock_years | pass |
|---|---|---|---|---|
| ALB | Albania | 12.42 | -0.12 | no |
| ARM | Armenia | 14.44 | -5.26 | no |
| BIH | Bosnia and Herzegovina | 14.39 | -0.51 | no |
| BMU | Bermuda | 20.73 | -3.02 | no |
| COM | Comoros | 13.05 | 4.74 | yes |
| CPV | Cabo Verde | 11.36 | 0.74 | yes |
| DOM | Dominican Republic | 8.25 | 3.19 | yes |
| GEO | Georgia | 9.95 | 11.20 | yes |
| GMB | Gambia, The | 11.33 | 3.35 | yes |
| GTM | Guatemala | 11.45 | 2.21 | yes |
| HND | Honduras | 17.80 | 3.09 | yes |
| HTI | Haiti | 14.51 | 2.23 | yes |
| KGZ | Kyrgyz Republic | 21.38 | 6.31 | yes |
| KIR | Kiribati | 8.43 | 5.87 | yes |
| LBN | Lebanon | 20.14 | 0.36 | yes |
| LSO | Lesotho | 29.84 | 2.72 | yes |
| MDA | Moldova | 21.52 | 0.55 | yes |
| MHL | Marshall Islands | 15.30 | -1.87 | no |
| MNE | Montenegro | 10.74 | -4.57 | no |
| NIC | Nicaragua | 11.01 | 3.69 | yes |
| NPL | Nepal | 19.56 | 5.74 | yes |
| PHL | Philippines | 10.27 | -0.40 | no |
| PSE | West Bank and Gaza | 14.11 | 0.13 | yes |
| SEN | Senegal | 8.65 | 2.98 | yes |
| SLV | El Salvador | 19.78 | -1.71 | no |
| TJK | Tajikistan | 31.40 | 4.26 | yes |
| TON | Tonga | 30.29 | -4.46 | no |
| UZB | Uzbekistan | 9.74 | 4.65 | yes |
| WSM | Samoa | 18.51 | 7.20 | yes |
| XKX | Kosovo | 17.06 | 5.34 | yes |
| ZWE | Zimbabwe | 8.64 | -2.54 | no |

## Interpretation

This is a descriptive structural-screen verdict using local WDI/OWID vintages.
It grades the predeclared pattern, not a causal effect of a single policy lever.

## Steelman

See `hypotheses/steelman/wdi_remittance_consumption_resilience_2009_2021.md`.
