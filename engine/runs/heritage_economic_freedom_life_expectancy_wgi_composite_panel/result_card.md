# Result card - heritage_economic_freedom_life_expectancy_wgi_composite_panel

**Verdict:** SUPPORTED - lagged proxy has expected sign + and p=0.02202

## Candidate Screen Source
- Queue rank: 22.
- Original candidate: `heritage_economic_freedom_life_expectancy_income_region_robustness`.
- Original controlled screen: SUPPORTED; q=0.004178782895145467.

## Panel Graduation Design
- Treatment proxy: within-year z-score composite of WGI regulatory quality, rule of law, and control of corruption lagged one year.
- Outcome: life expectancy at birth (world_bank_wdi:SP.DYN.LE00.IN).
- Estimator: country and year fixed effects with log PPP GDP per capita control.
- Standard errors: clustered by country.
- Gate: expected coefficient sign plus p <= 0.10 for support.

## Estimate
- Usable panel: 4627 observations, 195 countries, years 1998-2023.
- Coefficient on lagged proxy: 1.0082.
- Standard error: 0.44013.
- p-value: 0.022024.
- Expected sign: `+`.

## Leave-One-Region-Out
| Omitted region | Coef | p-value | n | countries | direction ok |
| --- | ---: | ---: | ---: | ---: | --- |
| Americas | 0.75657 | 0.2008 | 3502 | 147 | true |
| Asia-Pacific | 1.3886 | 0.040908 | 3313 | 139 | true |
| Europe | 1.6898 | 0.0041158 | 3151 | 132 | true |
| Middle East/North Africa | 0.9521 | 0.089185 | 3815 | 160 | true |
| Sub-Saharan Africa | 0.38978 | 0.20548 | 3107 | 130 | true |

## Methodology Status
This is a Worker E stronger panel artifact derived from a post-estimation HERITAGE candidate screen. It is not scoreboard evidence and should not be promoted without a matching pre-registration/spec audit.

## Provenance
Exact vintages and SHA-256 hashes are recorded in `manifest.yaml`. Re-run with `replication.py`.
