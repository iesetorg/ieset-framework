# School Tested Equalization Plan

Generated: 2026-10-11
Target tested prediction rows per school: `200`

## Methodology Gate

- Unit is scoreboard prediction rows, not net scores and not unique hypothesis IDs.
- Existing hidden linked claims are repaired before any new links are recommended.
- Only a hidden claim with a verified pre-run school forecast enters the existing-result repair queue; a later link needs a new prospective test.
- The plan does not change verdicts, polarity, school predictions, or score weights.

## Summary

- Schools tracked: 16
- Current tested range: 0-53
- Total tested gap to target: 3026
- Potential gap fillable by repairing hidden pre-run claims: 3
- Preregistered school predictions awaiting a first run: 3
- Gap requiring new prospective tests after possible repairs: 3023
- Blocker counts: `{'school_prediction_not_pre_run': 4561, 'school_score_eligible_false': 16, 'awaiting_first_run': 3, 'needs_successful_rerun': 3}`

## School Gaps

| school | tested | untested | hidden linked | pre-run hidden | future registered | public timing holds | public school-score holds | unlinked | gap | repair existing | prospective test gap | top blockers | top axes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| `post_keynesian` | 0 | 285 | 268 | 0 | 0 | 16 | 1 | 0 | 200 | 0 | 200 | school_prediction_not_pre_run (284), school_score_eligible_false (1) | unclassified (151), regulatory.trade_openness (23), fiscal.transfer_expansion (15), institutional.property_rights (14), monetary.monetary_expansion_direction (13) |
| `new_keynesian` | 0 | 286 | 267 | 0 | 0 | 18 | 1 | 0 | 200 | 0 | 200 | school_prediction_not_pre_run (285), school_score_eligible_false (1) | unclassified (151), monetary.monetary_expansion_direction (17), regulatory.trade_openness (16), institutional.rule_of_law (13), regulatory.labour_market_flexibility (13) |
| `marxist_leninist` | 0 | 283 | 265 | 0 | 0 | 17 | 1 | 0 | 200 | 0 | 200 | school_prediction_not_pre_run (282), school_score_eligible_false (1) | unclassified (147), regulatory.trade_openness (23), institutional.property_rights (19), fiscal.transfer_expansion (17), regulatory.product_market_competition (12) |
| `marxian` | 0 | 290 | 269 | 0 | 0 | 20 | 1 | 0 | 200 | 0 | 200 | school_prediction_not_pre_run (289), school_score_eligible_false (1) | unclassified (153), institutional.property_rights (17), monetary.monetary_expansion_direction (16), regulatory.trade_openness (15), fiscal.transfer_expansion (15) |
| `eco_socialist` | 0 | 292 | 276 | 0 | 0 | 15 | 1 | 0 | 200 | 0 | 200 | school_prediction_not_pre_run (291), school_score_eligible_false (1) | unclassified (155), institutional.property_rights (19), regulatory.trade_openness (16), fiscal.transfer_expansion (15), institutional.rule_of_law (11) |
| `developmentalism` | 0 | 301 | 280 | 1 | 0 | 20 | 1 | 0 | 200 | 1 | 199 | school_prediction_not_pre_run (299), needs_successful_rerun (1), school_score_eligible_false (1) | unclassified (150), regulatory.trade_openness (38), fiscal.transfer_expansion (27), institutional.rule_of_law (18), institutional.property_rights (15) |
| `democratic_socialist` | 0 | 287 | 269 | 0 | 0 | 17 | 1 | 0 | 200 | 0 | 200 | school_prediction_not_pre_run (286), school_score_eligible_false (1) | unclassified (147), regulatory.trade_openness (23), fiscal.transfer_expansion (18), institutional.property_rights (17), regulatory.labour_market_flexibility (15) |
| `degrowth` | 0 | 290 | 270 | 0 | 2 | 19 | 1 | 0 | 200 | 0 | 200 | school_prediction_not_pre_run (287), awaiting_first_run (2), school_score_eligible_false (1) | unclassified (156), institutional.property_rights (19), fiscal.transfer_expansion (17), regulatory.trade_openness (16), regulatory.labour_market_flexibility (11) |
| `social_democratic` | 1 | 301 | 281 | 0 | 1 | 19 | 1 | 0 | 199 | 0 | 199 | school_prediction_not_pre_run (299), school_score_eligible_false (1), awaiting_first_run (1) | unclassified (155), regulatory.trade_openness (27), fiscal.transfer_expansion (21), institutional.rule_of_law (16), regulatory.labour_market_flexibility (15) |
| `mmt` | 1 | 285 | 265 | 0 | 0 | 19 | 1 | 0 | 199 | 0 | 199 | school_prediction_not_pre_run (284), school_score_eligible_false (1) | unclassified (151), monetary.monetary_expansion_direction (19), institutional.property_rights (16), fiscal.transfer_expansion (15), regulatory.trade_openness (14) |
| `market_socialist` | 1 | 287 | 267 | 0 | 0 | 19 | 1 | 0 | 199 | 0 | 199 | school_prediction_not_pre_run (286), school_score_eligible_false (1) | unclassified (152), institutional.property_rights (23), regulatory.trade_openness (17), fiscal.transfer_expansion (15), regulatory.labour_market_flexibility (12) |
| `institutionalism` | 12 | 281 | 260 | 2 | 0 | 20 | 1 | 0 | 188 | 2 | 186 | school_prediction_not_pre_run (278), needs_successful_rerun (2), school_score_eligible_false (1) | unclassified (150), regulatory.trade_openness (32), institutional.rule_of_law (26), institutional.property_rights (20), regulatory.product_market_competition (16) |
| `chicago_monetarism` | 14 | 287 | 266 | 0 | 0 | 20 | 1 | 0 | 186 | 0 | 186 | school_prediction_not_pre_run (286), school_score_eligible_false (1) | unclassified (155), regulatory.trade_openness (33), monetary.monetary_expansion_direction (29), regulatory.product_market_competition (13), institutional.property_rights (11) |
| `austrian` | 40 | 259 | 236 | 0 | 0 | 22 | 1 | 0 | 160 | 0 | 160 | school_prediction_not_pre_run (258), school_score_eligible_false (1) | unclassified (159), regulatory.trade_openness (23), monetary.monetary_expansion_direction (18), regulatory.product_market_competition (16), institutional.property_rights (10) |
| `ordoliberal` | 52 | 268 | 244 | 0 | 0 | 23 | 1 | 0 | 148 | 0 | 148 | school_prediction_not_pre_run (267), school_score_eligible_false (1) | unclassified (163), regulatory.trade_openness (24), regulatory.product_market_competition (18), institutional.rule_of_law (18), institutional.property_rights (10) |
| `classical_liberal` | 53 | 301 | 270 | 0 | 0 | 30 | 1 | 0 | 147 | 0 | 147 | school_prediction_not_pre_run (300), school_score_eligible_false (1) | unclassified (165), regulatory.trade_openness (39), institutional.rule_of_law (22), regulatory.product_market_competition (18), institutional.property_rights (15) |

## First Repair Queue

| school | claim | hypothesis | reason | axis | runner |
| --- | ---: | --- | --- | --- | --- |
| `developmentalism` | 15 | `nova_industria_brasil_export_discipline_pattern_effect` | `needs_successful_rerun` | `regulatory.trade_openness` | `-` |
| `institutionalism` | 5 | `singapore_cpf_institutional_complementarity` | `needs_successful_rerun` | `institutional.rule_of_law` | `scripts/run_synth_did.py` |
| `institutionalism` | 10 | `zimbabwe_property_rights_output_link` | `needs_successful_rerun` | `institutional.property_rights` | `-` |

## First Repair IDs

Use this list for bounded rerun/repair waves; repeated IDs can affect multiple schools.
- `nova_industria_brasil_export_discipline_pattern_effect`
- `singapore_cpf_institutional_complementarity`
- `zimbabwe_property_rights_output_link`
