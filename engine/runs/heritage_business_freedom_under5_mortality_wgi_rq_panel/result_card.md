# Result card - heritage_business_freedom_under5_mortality_wgi_rq_panel

**Verdict:** PARTIAL - lagged proxy has expected sign - but p=0.1276 exceeds 0.1

## Candidate Screen Source
- Queue rank: 18.
- Original candidate: `heritage_business_freedom_under5_mortality_income_region_robustness`.
- Original controlled screen: SUPPORTED; q=0.0005579982071424246.

## Panel Graduation Design
- Treatment proxy: WGI regulatory quality estimate lagged one year.
- Outcome: under-5 mortality rate (world_bank_wdi:SH.DYN.MORT).
- Estimator: country and year fixed effects with log PPP GDP per capita control.
- Standard errors: clustered by country.
- Gate: expected coefficient sign plus p <= 0.10 for support.

## Estimate
- Usable panel: 4370 observations, 187 countries, years 1998-2023.
- Coefficient on lagged proxy: -5.083.
- Standard error: 3.3355.
- p-value: 0.1276.
- Expected sign: `-`.

## Leave-One-Region-Out
| Omitted region | Coef | p-value | n | countries | direction ok |
| --- | ---: | ---: | ---: | ---: | --- |
| Americas | -4.1088 | 0.32191 | 3469 | 147 | true |
| Asia-Pacific | -7.6569 | 0.078311 | 3296 | 139 | true |
| Europe | -8.4201 | 0.040306 | 3115 | 132 | true |
| Middle East/North Africa | -6.9883 | 0.069611 | 3772 | 160 | true |
| Sub-Saharan Africa | 1.0396 | 0.58457 | 3064 | 130 | false |

## Methodology Status
This is a Worker E stronger panel artifact derived from a post-estimation HERITAGE candidate screen. It is not scoreboard evidence and should not be promoted without a matching pre-registration/spec audit.

## Provenance
Exact vintages and SHA-256 hashes are recorded in `manifest.yaml`. Re-run with `replication.py`.
