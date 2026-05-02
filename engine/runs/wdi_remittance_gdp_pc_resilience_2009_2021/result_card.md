# Result card - wdi_remittance_gdp_pc_resilience_2009_2021

**Verdict:** supported - 19 of 37 countries passed (51.4%); median avg_gdp_pc_growth_shock_years = 0.34

## Predeclared Threshold

SUPPORTED if n>=25, at least 50% of high-remittance economies have non-negative average GDP-per-capita growth in shock years, and the median is >=0%. REFUTED if fewer than 40% pass or the median is below -2%. Otherwise PARTIAL.

Threshold expression: `n >= 25 AND pass_rate >= 0.50 AND median_avg_gdp_pc_growth_shock_years >= 0`

## Metrics

- n_countries: 37
- countries_passing: 19
- pass_rate: 0.5135135135135135
- median_avg_gdp_pc_growth_shock_years: 0.34033276811535984

## Country Panel

| country_iso3 | country_name | avg_remittances_pct_gdp | avg_gdp_pc_growth_shock_years | pass |
|---|---|---|---|---|
| ALB | Albania | 12.42 | 4.08 | yes |
| ARM | Armenia | 14.44 | -4.97 | no |
| BIH | Bosnia and Herzegovina | 14.39 | 2.08 | yes |
| BMU | Bermuda | 20.73 | -3.02 | no |
| COM | Comoros | 13.05 | -0.31 | no |
| CPV | Cabo Verde | 11.36 | -5.57 | no |
| DOM | Dominican Republic | 8.25 | 1.23 | yes |
| GEO | Georgia | 9.95 | 0.64 | yes |
| GMB | Gambia, The | 11.33 | 1.55 | yes |
| GTM | Guatemala | 11.45 | 0.61 | yes |
| GUY | Guyana | 8.93 | 22.12 | yes |
| HND | Honduras | 17.80 | -1.46 | no |
| HTI | Haiti | 14.51 | -1.09 | no |
| JAM | Jamaica | 15.74 | -2.61 | no |
| JOR | Jordan | 15.09 | 0.57 | yes |
| KGZ | Kyrgyz Republic | 21.38 | -1.30 | no |
| KIR | Kiribati | 8.43 | 0.60 | yes |
| LBN | Lebanon | 20.14 | -6.21 | no |
| LBR | Liberia | 13.28 | -0.05 | no |
| LSO | Lesotho | 29.84 | -3.37 | no |
| MDA | Moldova | 21.52 | 0.84 | yes |
| MHL | Marshall Islands | 15.30 | 3.11 | yes |
| MNE | Montenegro | 10.74 | -2.61 | no |
| NIC | Nicaragua | 11.01 | 0.34 | yes |
| NPL | Nepal | 19.56 | 0.88 | yes |
| PHL | Philippines | 10.27 | -2.05 | no |
| PSE | West Bank and Gaza | 14.11 | -1.12 | no |
| PYF | French Polynesia | 10.69 | -4.03 | no |
| SEN | Senegal | 8.65 | 0.98 | yes |
| SLV | El Salvador | 19.78 | 0.35 | yes |
| TJK | Tajikistan | 31.40 | 3.62 | yes |
| TON | Tonga | 30.29 | -1.42 | no |
| TUV | Tuvalu | 13.37 | -2.08 | no |
| UZB | Uzbekistan | 9.74 | 3.99 | yes |
| WSM | Samoa | 18.51 | -3.74 | no |
| XKX | Kosovo | 17.06 | 3.66 | yes |
| ZWE | Zimbabwe | 8.64 | 2.99 | yes |

## Interpretation

This is a descriptive structural-screen verdict using local WDI/OWID vintages.
It grades the predeclared pattern, not a causal effect of a single policy lever.

## Steelman

See `hypotheses/steelman/wdi_remittance_gdp_pc_resilience_2009_2021.md`.
