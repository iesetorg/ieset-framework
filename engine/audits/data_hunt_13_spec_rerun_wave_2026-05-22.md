# Data-Hunt 13-Spec Rerun Wave - 2026-05-22

## Summary

Reran the 13-spec data-hunt batch against the current `scripts/run_panel_fe.py`
runner with `--force`. All 13 specs produced real panel-FE verdict artifacts;
none are data-pending.

| Verdict | Count |
| --- | ---: |
| SUPPORTED | 4 |
| PARTIAL | 7 |
| REFUTED | 2 |
| INCONCLUSIVE_DATA_PENDING | 0 |
| Total | 13 |

Targeted hypothesis-schema validation passed for all 13 specs.

## Results

| hypothesis | verdict | coefficient | p-value | observations | countries | note |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| `bis_credit_gap_governance_crisis_amplifier_panel` | REFUTED | -0.02156 | 0.0930 | 1,031 | 41 | Credit-gap x weak-governance interaction is negative, opposite the registered positive-amplifier claim. |
| `bis_corporate_dsr_manufacturing_drag_panel` | SUPPORTED | -0.05208 | 0.0798 | 401 | 17 | Higher corporate debt-service burden predicts weaker manufacturing real value-added growth. |
| `bis_credit_gap_reer_appreciation_export_squeeze_panel` | REFUTED | +0.007529 | 0.0286 | 1,098 | 40 | Interaction is positive, opposite the registered export-squeeze claim. |
| `bis_reer_appreciation_trade_open_disinflation_panel` | PARTIAL | -0.000994 | 0.257 | 1,230 | 41 | Direction is aligned with disinflation channel but not statistically decisive. |
| `oecd_socx_welfare_employment_capacity_interaction_panel` | PARTIAL | +0.09751 | 0.208 | 980 | 42 | Capacity interaction is right-signed but not decisive. |
| `oecd_almp_epl_low_education_unemployment_interaction_panel` | PARTIAL | +1.499 | 0.411 | 446 | 24 | Interaction is right-signed but not decisive. |
| `eurostat_power_cost_manufacturing_real_gva_panel` | PARTIAL | +0.01302 | 0.601 | 521 | 30 | Estimate is not aligned with the expected drag and is not decisive. |
| `eurostat_unemployment_gini_stabilizer_panel` | SUPPORTED | +0.2344 | 0.000868 | 354 | 30 | Higher unemployment predicts higher market-income inequality, consistent with stabilizer/redistribution pressure. |
| `eurostat_power_cost_unemployment_slack_panel` | PARTIAL | +0.005075 | 0.253 | 485 | 29 | Right-signed unemployment-slack channel but not decisive. |
| `wits_tariff_cuts_import_variety_panel` | PARTIAL | -0.000898 | 0.352 | 1,030 | 39 | Tariff direction is aligned with import-variety expansion but not decisive. |
| `wits_export_concentration_hightech_drag_panel` | SUPPORTED | -5.286 | 0.0000791 | 580 | 39 | Export concentration strongly predicts weaker high-tech export performance. |
| `wipo_patent_applications_hightech_export_followthrough_panel` | SUPPORTED | +0.1756 | 0.0387 | 444 | 30 | Resident patenting predicts stronger high-tech export follow-through. |
| `owid_fossil_subsidy_hightech_export_drag_panel` | PARTIAL | +0.03032 | 0.224 | 169 | 21 | Fossil-subsidy proxy is not decisive and points opposite the registered drag claim. |

## Interpretation

The strongest scoreboard candidates from this wave are:

- `wits_export_concentration_hightech_drag_panel`
- `wipo_patent_applications_hightech_export_followthrough_panel`
- `bis_corporate_dsr_manufacturing_drag_panel`

The cleanest cautionary/refutation candidates are:

- `bis_credit_gap_governance_crisis_amplifier_panel`
- `bis_credit_gap_reer_appreciation_export_squeeze_panel`

The seven partials should not be mapped as wins or losses yet. They are useful
for identifying follow-up designs: richer lags, interaction-specific marginal
effects, or tighter treatment definitions.
