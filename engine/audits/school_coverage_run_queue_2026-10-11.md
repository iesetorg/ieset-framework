# School Coverage Run Queue

Generated: 2026-10-11

## Methodology Gate

- This queue ranks hidden linked hypotheses only where a reciprocal school forecast was frozen before the first run.
- Historical school links, school-score holds, and unrun future registrations remain visible but cannot enter this existing-result repair queue.
- It does not change verdicts, school predictions, polarity, or net scores.
- Repair eligible pre-run pending hypotheses first, then preregister new school predictions and tests for the remaining gap.
- Attaching a school to an existing result after its first run does not create an advance result.

## Summary

- Under-covered schools: 16
- Pending candidates with coverage benefit: 3
- Top blocker types: needs_successful_rerun=3
- Claim links held outside the repair queue: `{'school_prediction_not_pre_run': 4561, 'school_score_eligible_false': 16, 'awaiting_first_run': 3}`
- Linked gap remaining after pending runs: 0
- Tested gap remaining after exhausting pending runs: 783

## Highest-Leverage Queue

| rank | hypothesis | score | schools helped | axis | blocker |
| ---: | --- | ---: | ---: | --- | --- |
| 1 | `nova_industria_brasil_export_discipline_pattern_effect` | 2.000 | 1 (`developmentalism`) | `regulatory.trade_openness` | needs_successful_rerun |
| 2 | `singapore_cpf_institutional_complementarity` | 1.800 | 1 (`institutionalism`) | `institutional.rule_of_law` | needs_successful_rerun |
| 3 | `zimbabwe_property_rights_output_link` | 1.800 | 1 (`institutionalism`) | `institutional.property_rights` | needs_successful_rerun |

## First Batch IDs

Use the companion `.ids` file for automation input. The first 20 IDs are:
- `nova_industria_brasil_export_discipline_pattern_effect`
- `singapore_cpf_institutional_complementarity`
- `zimbabwe_property_rights_output_link`
