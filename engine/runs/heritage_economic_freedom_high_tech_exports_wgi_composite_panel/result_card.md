# Result card - heritage_economic_freedom_high_tech_exports_wgi_composite_panel

**Verdict:** PARTIAL - lagged proxy has expected sign + but p=0.1648 exceeds 0.1

## Candidate Screen Source
- Queue rank: 20.
- Original candidate: `heritage_economic_freedom_high_tech_exports_income_region_robustness`.
- Original controlled screen: SUPPORTED; q=0.0026557639799479767.

## Panel Graduation Design
- Treatment proxy: within-year z-score composite of WGI regulatory quality, rule of law, and control of corruption lagged one year.
- Outcome: high-technology exports share (world_bank_wdi:TX.VAL.TECH.MF.ZS).
- Estimator: country and year fixed effects with log PPP GDP per capita control.
- Standard errors: clustered by country.
- Gate: expected coefficient sign plus p <= 0.10 for support.

## Estimate
- Usable panel: 2494 observations, 180 countries, years 2007-2023.
- Coefficient on lagged proxy: 1.92.
- Standard error: 1.3817.
- p-value: 0.16478.
- Expected sign: `+`.

## Leave-One-Region-Out
| Omitted region | Coef | p-value | n | countries | direction ok |
| --- | ---: | ---: | ---: | ---: | --- |
| Americas | 3.2615 | 0.065326 | 1898 | 139 | true |
| Asia-Pacific | 2.2849 | 0.14984 | 1902 | 133 | true |
| Europe | 0.0232 | 0.9847 | 1633 | 124 | true |
| Middle East/North Africa | 2.4646 | 0.090601 | 2146 | 152 | true |
| Sub-Saharan Africa | 2.8549 | 0.06853 | 1813 | 124 | true |

## Methodology Status
This is a Worker E stronger panel artifact derived from a post-estimation HERITAGE candidate screen. It is not scoreboard evidence and should not be promoted without a matching pre-registration/spec audit.

## Provenance
Exact vintages and SHA-256 hashes are recorded in `manifest.yaml`. Re-run with `replication.py`.
