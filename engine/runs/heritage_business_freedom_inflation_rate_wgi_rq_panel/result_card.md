# Result card - heritage_business_freedom_inflation_rate_wgi_rq_panel

**Verdict:** PARTIAL - lagged proxy has expected sign - but p=0.2174 exceeds 0.1

## Candidate Screen Source
- Queue rank: 17.
- Original candidate: `heritage_business_freedom_inflation_rate_income_region_robustness`.
- Original controlled screen: SUPPORTED; q=0.0004647595345020366.

## Panel Graduation Design
- Treatment proxy: WGI regulatory quality estimate lagged one year.
- Outcome: annual CPI inflation (world_bank_wdi:FP.CPI.TOTL.ZG).
- Estimator: country and year fixed effects with log PPP GDP per capita control.
- Standard errors: clustered by country.
- Gate: expected coefficient sign plus p <= 0.10 for support.

## Estimate
- Usable panel: 4185 observations, 187 countries, years 1998-2023.
- Coefficient on lagged proxy: -3.838.
- Standard error: 3.1112.
- p-value: 0.21742.
- Expected sign: `-`.

## Leave-One-Region-Out
| Omitted region | Coef | p-value | n | countries | direction ok |
| --- | ---: | ---: | ---: | ---: | --- |
| Americas | -5.7697 | 0.15139 | 3313 | 145 | true |
| Asia-Pacific | -4.1776 | 0.34326 | 3171 | 138 | true |
| Europe | -5.1212 | 0.28471 | 2941 | 130 | true |
| Middle East/North Africa | -3.4124 | 0.36177 | 3614 | 158 | true |
| Sub-Saharan Africa | -2.8117 | 0.068685 | 2957 | 129 | true |

## Methodology Status
This is a Worker E stronger panel artifact derived from a post-estimation HERITAGE candidate screen. It is not scoreboard evidence and should not be promoted without a matching pre-registration/spec audit.

## Provenance
Exact vintages and SHA-256 hashes are recorded in `manifest.yaml`. Re-run with `replication.py`.
