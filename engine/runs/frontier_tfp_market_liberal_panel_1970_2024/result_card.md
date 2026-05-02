# Result card — frontier_tfp_market_liberal_panel_1970_2024

**Verdict:** partial — TWFE β_RQ=+0.0048 (SE 0.0031, p=0.128, n=608), R²_within=0.525. Does not meet falsification threshold.

## Design

OECD + high-income Asian panel 1970-2019. Outcome: 5-year-forward
annualised log TFP growth (PWT `rtfpna`). Treatment: WGI Regulatory Quality
(`GOV_WGI_RQ.EST`) as proxy for market liberalisation / low state interference.
Controls: log initial TFP, log GDP per capita. Estimator: TWFE with country and
year fixed effects, clustered SE by country.

## Threshold

SUPPORTED if β_RQ > 0 and p < 0.05 in primary TWFE.
REFUTED if β_RQ < 0 and p < 0.05.
Otherwise PARTIAL.

## Metrics

| Metric | Value |
|---|---|
| Observations | 608 |
| Countries | 38 |
| β_RQ | +0.0048 |
| SE | 0.0031 |
| 95% CI | [-0.0014, +0.0109] |
| p-value | 0.128 |
| R² within | 0.525 |

## Limitations

- WGI Regulatory Quality is a perception-based governance indicator, not a direct
  product-market-regulation or state-ownership measure.
- OECD PMR or Fraser EFW would be sharper proxies but are not available in local
  vintages.
- TWFE with staggered adoption and heterogeneous treatment effects may bias
  estimates (Goodman-Bacon 2021).
- 5-year-forward windows shrink sample at panel ends.

## Next robustness checks

- Re-run with 10-year-forward growth.
- Add country-specific time trends.
- Use alternative institution proxies (WGI Rule of Law, V-Dem liberal component).
- Restrict to post-1990 panel where WGI coverage is denser.
