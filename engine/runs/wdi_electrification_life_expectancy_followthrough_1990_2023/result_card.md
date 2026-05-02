# Result card - wdi_electrification_life_expectancy_followthrough_1990_2023

**Verdict:** supported - 37 of 56 countries passed (66.1%); median life_expectancy_gain_years = 10.80

## Predeclared Threshold

SUPPORTED if n>=40, at least 65% of selected countries gain >=8 life-expectancy years, and the median gain is >=8 years. REFUTED if fewer than 45% pass or the median gain is <5 years. Otherwise PARTIAL.

Threshold expression: `n >= 40 AND pass_rate >= 0.65 AND median_life_expectancy_gain_years >= 8`

## Metrics

- n_countries: 56
- countries_passing: 37
- pass_rate: 0.6607142857142857
- median_life_expectancy_gain_years: 10.800500000000003

## Country Panel

| country_iso3 | country_name | electricity_access_gain_pp | life_expectancy_gain_years | pass |
|---|---|---|---|---|
| AFG | Afghanistan | 80.90 | 20.92 | yes |
| BEN | Benin | 42.50 | 7.75 | no |
| BGD | Bangladesh | 85.21 | 18.85 | yes |
| BLZ | Belize | 32.60 | 4.00 | no |
| BOL | Bolivia | 39.77 | 11.78 | yes |
| BTN | Bhutan | 68.80 | 17.16 | yes |
| BWA | Botswana | 65.90 | 9.06 | yes |
| CIV | Cote d'Ivoire | 35.90 | 9.15 | yes |
| CMR | Cameroon | 43.00 | 9.35 | yes |
| COM | Comoros | 60.90 | 11.16 | yes |
| CPV | Cabo Verde | 40.00 | 12.19 | yes |
| ERI | Eritrea | 31.50 | 18.89 | yes |
| ETH | Ethiopia | 42.70 | 22.20 | yes |
| FJI | Fiji | 32.40 | 2.26 | no |
| FSM | Micronesia, Fed. Sts. | 40.90 | 3.48 | no |
| GHA | Ghana | 58.90 | 10.10 | yes |
| GIN | Guinea | 34.70 | 13.49 | yes |
| GMB | Gambia, The | 49.20 | 14.58 | yes |
| GNB | Guinea-Bissau | 39.20 | 17.19 | yes |
| GTM | Guatemala | 39.20 | 10.84 | yes |
| HND | Honduras | 40.82 | 7.70 | no |
| IDN | Indonesia | 50.50 | 7.90 | no |
| IND | India | 48.60 | 13.38 | yes |
| KEN | Kenya | 65.30 | 5.31 | no |
| KHM | Cambodia | 76.33 | 15.46 | yes |
| KIR | Kiribati | 40.30 | 5.45 | no |
| LAO | Lao PDR | 65.50 | 14.93 | yes |
| LSO | Lesotho | 53.00 | -1.94 | no |
| MAR | Morocco | 50.80 | 12.92 | yes |
| MDG | Madagascar | 30.20 | 11.49 | yes |
| MHL | Marshall Islands | 31.48 | 5.19 | no |
| MLI | Mali | 48.30 | 13.90 | yes |
| MMR | Myanmar | 34.90 | 9.73 | yes |
| MNG | Mongolia | 32.70 | 13.32 | yes |
| MRT | Mauritania | 31.20 | 10.40 | yes |
| NAM | Namibia | 30.30 | 6.03 | no |
| NGA | Nigeria | 33.90 | 8.73 | yes |
| NPL | Nepal | 76.10 | 15.58 | yes |
| PHL | Philippines | 32.60 | 5.45 | no |
| PRK | Korea, Dem. People's Rep. | 31.50 | 3.16 | no |
| RWA | Rwanda | 61.60 | 20.02 | yes |
| SDN | Sudan | 33.20 | 10.83 | yes |
| SEN | Senegal | 48.20 | 12.01 | yes |
| SLB | Solomon Islands | 65.60 | 4.33 | no |
| SOM | Somalia, Fed. Rep. | 48.20 | 11.92 | yes |
| SWZ | Eswatini | 66.00 | 2.96 | no |
| TGO | Togo | 43.90 | 8.17 | yes |
| TLS | Timor-Leste | 82.20 | 22.50 | yes |
| TZA | Tanzania | 41.50 | 15.01 | yes |
| UGA | Uganda | 45.90 | 20.69 | yes |
| VCT | St. Vincent and the Grenadines | 33.20 | 0.58 | no |
| VUT | Vanuatu | 43.60 | 4.79 | no |
| YEM | Yemen, Rep. | 39.50 | 10.77 | yes |
| ZAF | South Africa | 30.10 | 3.20 | no |
| ZMB | Zambia | 37.20 | 18.15 | yes |
| ZWE | Zimbabwe | 33.80 | 4.46 | no |

## Interpretation

This is a descriptive structural-screen verdict using local WDI/OWID vintages.
It grades the predeclared pattern, not a causal effect of a single policy lever.

## Steelman

See `hypotheses/steelman/wdi_electrification_life_expectancy_followthrough_1990_2023.md`.
