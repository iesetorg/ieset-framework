# Result card - heritage_property_rights_high_tech_exports_wgi_rl_panel

**Verdict:** PARTIAL - lagged proxy has expected sign + but p=0.4171 exceeds 0.1

## Candidate Screen Source
- Queue rank: 32.
- Original candidate: `heritage_property_rights_high_tech_exports_income_region_robustness`.
- Original controlled screen: SUPPORTED; q=0.013880438376879302.

## Panel Graduation Design
- Treatment proxy: WGI rule of law estimate lagged one year.
- Outcome: high-technology exports share (world_bank_wdi:TX.VAL.TECH.MF.ZS).
- Estimator: country and year fixed effects with log PPP GDP per capita control.
- Standard errors: clustered by country.
- Gate: expected coefficient sign plus p <= 0.10 for support.

## Estimate
- Usable panel: 2494 observations, 180 countries, years 2007-2023.
- Coefficient on lagged proxy: 1.2874.
- Standard error: 1.5862.
- p-value: 0.41709.
- Expected sign: `+`.

## Leave-One-Region-Out
| Omitted region | Coef | p-value | n | countries | direction ok |
| --- | ---: | ---: | ---: | ---: | --- |
| Americas | 2.9374 | 0.074134 | 1898 | 139 | true |
| Asia-Pacific | 1.7699 | 0.22413 | 1902 | 133 | true |
| Europe | 0.51205 | 0.6625 | 1633 | 124 | true |
| Middle East/North Africa | 2.4415 | 0.074055 | 2146 | 152 | true |
| Sub-Saharan Africa | 3.143 | 0.032416 | 1813 | 124 | true |

## Methodology Status
This is a Worker E stronger panel artifact derived from a post-estimation HERITAGE candidate screen. It is not scoreboard evidence and should not be promoted without a matching pre-registration/spec audit.

## Provenance
Exact vintages and SHA-256 hashes are recorded in `manifest.yaml`. Re-run with `replication.py`.
