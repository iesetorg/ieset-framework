# Result card — product_market_regulation_tfp_30yr_panel

**Verdict:** partial — TWFE β_RQ=-0.0035 (SE 0.0046, p=0.448, n=1872), R²=0.428. Does not meet falsification threshold.

## Design

Broad panel 1990-2019. Outcome: 5-year-forward annualised log TFP growth
(PWT `rtfpna`). Treatment: WGI Regulatory Quality (`GOV_WGI_RQ.EST`) as proxy for
low product-market regulation / state interference. Controls: log initial TFP,
human capital (`hc`), log capital per worker, log GDP per capita. Estimator:
TWFE with country and year fixed effects, clustered SE by country.

## Threshold

SUPPORTED if β_RQ > 0 and p < 0.05.
REFUTED if β_RQ < 0 and p < 0.05.
Otherwise PARTIAL.

## Metrics

| Metric | Value |
|---|---|
| Observations | 1872 |
| Countries | 117 |
| β_RQ | -0.0035 |
| SE | 0.0046 |
| 95% CI | [-0.0124, +0.0055] |
| p-value | 0.448 |
| R² within | 0.428 |

## Limitations

- WGI Regulatory Quality is a governance perception index, not a direct
  product-market-regulation measure. OECD PMR or Fraser EFW would be sharper.
- PWT TFP is a residual and sensitive to measurement assumptions.
- TWFE with heterogeneous treatment effects may bias estimates.
- Human capital (`hc`) is based on years-of-schooling returns, not quality-adjusted.

## Next robustness checks

- Re-run with OECD-only sample.
- Use 10-year-forward TFP growth.
- Add country-specific time trends.
- Test alternative proxies (WGI Rule of Law, V-Dem liberal component).
