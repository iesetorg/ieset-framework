# Result card - heritage_business_freedom_private_consumption_pc_wgi_rq_panel

**Verdict:** SUPPORTED - lagged proxy has expected sign + and p=0.02643

## Candidate Screen Source
- Queue rank: 28.
- Original candidate: `heritage_business_freedom_private_consumption_pc_income_region_robustness`.
- Original controlled screen: SUPPORTED; q=0.011298529680877944.

## Panel Graduation Design
- Treatment proxy: WGI regulatory quality estimate lagged one year.
- Outcome: log private consumption per capita (world_bank_wdi:NE.CON.PRVT.PC.KD).
- Estimator: country and year fixed effects with log PPP GDP per capita control.
- Standard errors: clustered by country.
- Gate: expected coefficient sign plus p <= 0.10 for support.

## Estimate
- Usable panel: 3603 observations, 170 countries, years 1998-2023.
- Coefficient on lagged proxy: 0.058172.
- Standard error: 0.026194.
- p-value: 0.026432.
- Expected sign: `+`.

## Leave-One-Region-Out
| Omitted region | Coef | p-value | n | countries | direction ok |
| --- | ---: | ---: | ---: | ---: | --- |
| Americas | 0.056855 | 0.10622 | 2919 | 137 | true |
| Asia-Pacific | 0.069161 | 0.037015 | 2760 | 127 | true |
| Europe | 0.045602 | 0.21683 | 2394 | 114 | true |
| Middle East/North Africa | 0.062213 | 0.009932 | 3093 | 142 | true |
| Sub-Saharan Africa | 0.071687 | 0.015803 | 2526 | 116 | true |

## Methodology Status
This is a Worker E stronger panel artifact derived from a post-estimation HERITAGE candidate screen. It is not scoreboard evidence and should not be promoted without a matching pre-registration/spec audit.

## Provenance
Exact vintages and SHA-256 hashes are recorded in `manifest.yaml`. Re-run with `replication.py`.
