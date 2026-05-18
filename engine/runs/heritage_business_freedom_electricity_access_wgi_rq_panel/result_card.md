# Result card - heritage_business_freedom_electricity_access_wgi_rq_panel

**Verdict:** PARTIAL - lagged proxy is wrong-signed for expected sign + and p=0.4028

## Candidate Screen Source
- Queue rank: 16.
- Original candidate: `heritage_business_freedom_electricity_access_income_region_robustness`.
- Original controlled screen: SUPPORTED; q=0.00042999740027875247.

## Panel Graduation Design
- Treatment proxy: WGI regulatory quality estimate lagged one year.
- Outcome: access to electricity (% of population) (world_bank_wdi:EG.ELC.ACCS.ZS).
- Estimator: country and year fixed effects with log PPP GDP per capita control.
- Standard errors: clustered by country.
- Gate: expected coefficient sign plus p <= 0.10 for support.

## Estimate
- Usable panel: 4474 observations, 194 countries, years 1998-2023.
- Coefficient on lagged proxy: -1.327.
- Standard error: 1.5861.
- p-value: 0.40283.
- Expected sign: `+`.

## Leave-One-Region-Out
| Omitted region | Coef | p-value | n | countries | direction ok |
| --- | ---: | ---: | ---: | ---: | --- |
| Americas | -1.8627 | 0.38486 | 3411 | 146 | false |
| Asia-Pacific | -0.91581 | 0.49578 | 3245 | 138 | false |
| Europe | -0.67436 | 0.73826 | 3073 | 132 | false |
| Middle East/North Africa | -0.9711 | 0.62055 | 3717 | 159 | false |
| Sub-Saharan Africa | -1.988 | 0.35459 | 3026 | 129 | false |

## Methodology Status
This is a Worker E stronger panel artifact derived from a post-estimation HERITAGE candidate screen. It is not scoreboard evidence and should not be promoted without a matching pre-registration/spec audit.

## Provenance
Exact vintages and SHA-256 hashes are recorded in `manifest.yaml`. Re-run with `replication.py`.
