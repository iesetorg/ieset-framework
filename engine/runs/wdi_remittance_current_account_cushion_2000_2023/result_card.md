# Result card - wdi_remittance_current_account_cushion_2000_2023

**Verdict:** supported - 33 of 38 countries passed (86.8%); median avg_current_account_pct_gdp = -6.20

## Predeclared Threshold

SUPPORTED if n>=25, at least 70% of high-remittance economies average no worse than -10% of GDP on the current account, and the median average is >=-7%. REFUTED if fewer than 50% pass or the median is below -12%. Otherwise PARTIAL.

Threshold expression: `n >= 25 AND pass_rate >= 0.70 AND median_avg_current_account_pct_gdp >= -7`

## Metrics

- n_countries: 38
- countries_passing: 33
- pass_rate: 0.868421052631579
- median_avg_current_account_pct_gdp: -6.204269913299112

## Country Panel

| country_iso3 | country_name | avg_remittances_pct_gdp | avg_current_account_pct_gdp | pass |
|---|---|---|---|---|
| ALB | Albania | 12.42 | -8.41 | yes |
| ARM | Armenia | 14.44 | -6.73 | yes |
| BIH | Bosnia and Herzegovina | 14.39 | -8.11 | yes |
| BMU | Bermuda | 20.73 | 13.51 | yes |
| COM | Comoros | 13.05 | -3.24 | yes |
| CPV | Cabo Verde | 11.36 | -8.81 | yes |
| DOM | Dominican Republic | 8.25 | -3.05 | yes |
| GEO | Georgia | 9.95 | -9.86 | yes |
| GMB | Gambia, The | 11.33 | -4.21 | yes |
| GTM | Guatemala | 11.45 | -1.99 | yes |
| GUY | Guyana | 8.93 | -8.37 | yes |
| HND | Honduras | 17.80 | -5.66 | yes |
| HTI | Haiti | 14.51 | -1.75 | yes |
| JAM | Jamaica | 15.74 | -6.55 | yes |
| JOR | Jordan | 15.09 | -6.47 | yes |
| KGZ | Kyrgyz Republic | 21.38 | -9.27 | yes |
| KIR | Kiribati | 8.43 | 8.83 | yes |
| LBN | Lebanon | 20.14 | -19.73 | no |
| LBR | Liberia | 13.28 | -20.26 | no |
| LSO | Lesotho | 29.84 | -3.33 | yes |
| MDA | Moldova | 21.52 | -8.23 | yes |
| MHL | Marshall Islands | 15.30 | 3.70 | yes |
| MNE | Montenegro | 10.74 | -19.24 | no |
| NIC | Nicaragua | 11.01 | -8.72 | yes |
| NPL | Nepal | 19.56 | -0.12 | yes |
| PHL | Philippines | 10.27 | 0.94 | yes |
| PSE | West Bank and Gaza | 14.11 | -15.43 | no |
| PYF | French Polynesia | 10.69 | 1.59 | yes |
| SEN | Senegal | 8.65 | -8.09 | yes |
| SLV | El Salvador | 19.78 | -3.88 | yes |
| TJK | Tajikistan | 31.40 | -5.46 | yes |
| TON | Tonga | 30.29 | -10.93 | no |
| TUV | Tuvalu | 13.37 | -9.16 | yes |
| UZB | Uzbekistan | 9.74 | 1.48 | yes |
| WSM | Samoa | 18.51 | -5.48 | yes |
| XKX | Kosovo | 17.06 | -8.36 | yes |
| YEM | Yemen, Rep. | 8.45 | -3.74 | yes |
| ZWE | Zimbabwe | 8.64 | -5.94 | yes |

## Interpretation

This is a descriptive structural-screen verdict using local WDI/OWID vintages.
It grades the predeclared pattern, not a causal effect of a single policy lever.

## Steelman

See `hypotheses/steelman/wdi_remittance_current_account_cushion_2000_2023.md`.
