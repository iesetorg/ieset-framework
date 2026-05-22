# Data Hunt 13-Spec Campaign - 2026-05-21T14:02:10+00:00

## Counts
- PARTIAL: 7
- REFUTED: 2
- SUPPORTED: 4

## Results

| hypothesis_id | verdict | coef | p | n | countries |
|---|---:|---:|---:|---:|---:|
| `bis_credit_gap_governance_crisis_amplifier_panel` | REFUTED - coef=-0.02156 (sign opposite claim +), p=0.093 | -0.0215559 | 0.09298 | 1031 | 41 |
| `bis_corporate_dsr_manufacturing_drag_panel` | SUPPORTED - coef=-0.05208 (sign matches claim -), p=0.0798 | -0.0520781 | 0.07976 | 401 | 17 |
| `bis_credit_gap_reer_appreciation_export_squeeze_panel` | REFUTED - coef=+0.007529 (sign opposite claim -), p=0.0286 | 0.00752913 | 0.02857 | 1098 | 40 |
| `bis_reer_appreciation_trade_open_disinflation_panel` | PARTIAL - coef=-0.0009935, p=0.257 (above α=0.1); direction inconclusive | -0.000993524 | 0.2571 | 1230 | 41 |
| `oecd_socx_welfare_employment_capacity_interaction_panel` | PARTIAL - coef=+0.09751, p=0.208 (above α=0.1); direction inconclusive | 0.0975061 | 0.2078 | 980 | 42 |
| `oecd_almp_epl_low_education_unemployment_interaction_panel` | PARTIAL - coef=+1.499, p=0.411 (above α=0.1); direction inconclusive | 1.49897 | 0.4109 | 446 | 24 |
| `eurostat_power_cost_manufacturing_real_gva_panel` | PARTIAL - coef=+0.01302, p=0.601 (above α=0.1); direction inconclusive | 0.0130172 | 0.6008 | 521 | 30 |
| `eurostat_unemployment_gini_stabilizer_panel` | SUPPORTED - coef=+0.2344 (sign matches claim +), p=0.000868 | 0.234375 | 0.0008676 | 354 | 30 |
| `eurostat_power_cost_unemployment_slack_panel` | PARTIAL - coef=+0.005075, p=0.253 (above α=0.1); direction inconclusive | 0.00507528 | 0.2525 | 485 | 29 |
| `wits_tariff_cuts_import_variety_panel` | PARTIAL - coef=-0.000898, p=0.352 (above α=0.1); direction inconclusive | -0.000897999 | 0.3522 | 1030 | 39 |
| `wits_export_concentration_hightech_drag_panel` | SUPPORTED - coef=-5.286 (sign matches claim -), p=7.91e-05 | -5.28583 | 7.907e-05 | 580 | 39 |
| `wipo_patent_applications_hightech_export_followthrough_panel` | SUPPORTED - coef=+0.1756 (sign matches claim +), p=0.0387 | 0.175556 | 0.0387 | 444 | 30 |
| `owid_fossil_subsidy_hightech_export_drag_panel` | PARTIAL - coef=+0.03032, p=0.224 (above α=0.1); direction inconclusive | 0.030319 | 0.2243 | 169 | 21 |

## Notes

- BOJ monetary-transmission hypotheses intentionally excluded from this campaign pending date parsing verification.
- Existing unrelated dirty files in the full workspace were not modified except campaign outputs for the 13 new hypotheses.
