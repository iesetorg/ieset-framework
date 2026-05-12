# Scoreboard Conversion Queue B1

Date: 2026-05-12
Agent: Group 2 / Agent B1
Scope: queue only; no position or hypothesis files changed.

## Inputs Inspected

- `engine/audits/throughput_scoreboard_conversion_2026-05-12.md`
- `engine/audits/throughput_scoreboard_conversion_2026-05-12.json`
- `engine/audits/scoreboard_prediction_outcome_audit_2026-05-12_after_throughput.md`
- `engine/audits/scoreboard_prediction_outcome_audit_2026-05-12_after_mapping_wave1.md`
- `engine/audits/scoreboard_conversion_workplan_2026-05-12.md`
- `engine/audits/duplicate_broad_panel_upgrade_plan_2026-05-12.md`
- `engine/audits/cross_school_next50_results_2026-05-12.md`
- `engine/audits/cross_school_next50_swarm_cleanup_and_next_frontier_2026-05-12.md`

## Selection Rule

Pick the next safest conversion candidates from the latest outputs by requiring:

1. Verdict-bearing and decisive: `SUPPORTED` or `REFUTED`, not `PARTIAL` or inconclusive.
2. No duplicate coefficient-fingerprint hold in the throughput audit.
3. Complete run artifact coverage in the cross-school batch.
4. Clear school set from the generated cross-school result inventory.
5. No position edits yet: queue must specify the exact schools and reciprocal mapping work, not perform it.

This selects 25 cross-school candidates: 13 supported and 12 refuted. The 25 partial cross-school results are deliberately deferred to interpretation QA because directional partials can silently move school scores. The throughput audit still has 28 `needs_position_claim_mapping` items, but many are zero-link legacy/case-study results with broader associational flags or missing hypothesis paths; they are less safe than the structurally clean cross-school decisive subset.

## Conversion Buckets

| bucket | count | meaning |
| --- | ---: | --- |
| `map_now_cross_school_supported` | 13 | Add school claims predicting the hypothesis should be supported, then add reciprocal `covers_claims`; current verdict supports those claims. |
| `map_now_cross_school_refuted` | 12 | Add school claims predicting the hypothesis should be supported, then add reciprocal `covers_claims`; current verdict refutes those claims. |
| `defer_cross_school_partial_direction_qa` | 25 | Do not score yet; partial direction needs explicit aligned/inverted/neutral treatment. |
| `hold_duplicate_broad_panel_qa` | 18 | From throughput audit; do not map until duplicate evidence path is repaired. |
| `hold_broad_panel_upgrade` | 2 | From throughput audit; broad proxy must be sharpened before conversion. |

## Selected Queue

Mapping instruction for every selected row:

- Create one narrow falsifiable claim in each listed school if no exact existing claim already matches the generated hypothesis.
- Use `linked_hypothesis_id: <hypothesis>`.
- Use `school_prediction: supported`.
- Use `claim_polarity: aligned`.
- Add reciprocal `covers_claims` entries in the hypothesis YAML after positions are edited.
- Keep evidence quality as associational in scoreboard recompute; these are clean for mapping but still broad cross-country panels.

| priority | hypothesis | verdict | schools to map | bucket | QA flags |
| ---: | --- | --- | --- | --- | --- |
| 1 | `cross_school_efw_growth_market_order_1990_2023` | supported | `austrian`, `classical_liberal`, `chicago_monetarism`, `ordoliberal` | `map_now_cross_school_supported` | broad associational panel; no duplicate flag |
| 2 | `cross_school_efw_private_investment_market_order_1990_2023` | supported | `austrian`, `classical_liberal`, `ordoliberal` | `map_now_cross_school_supported` | broad associational panel; no duplicate flag |
| 3 | `cross_school_sound_money_inflation_reduction_1990_2023` | supported | `austrian`, `chicago_monetarism` | `map_now_cross_school_supported` | broad associational panel; no duplicate flag |
| 4 | `cross_school_rule_of_law_private_credit_depth_1996_2023` | supported | `ordoliberal`, `classical_liberal` | `map_now_cross_school_supported` | broad associational panel; no duplicate flag |
| 5 | `cross_school_regulatory_quality_private_investment_1996_2023` | supported | `ordoliberal`, `empirical_pragmatist` | `map_now_cross_school_supported` | broad associational panel; no duplicate flag |
| 6 | `cross_school_trade_openness_growth_1990_2023` | supported | `classical_liberal`, `developmentalism` | `map_now_cross_school_supported` | broad associational panel; no duplicate flag |
| 7 | `cross_school_private_credit_manufacturing_financialisation_1990_2023` | supported | `marxian`, `market_socialist`, `post_keynesian` | `map_now_cross_school_supported` | broad associational panel; no duplicate flag |
| 8 | `cross_school_private_credit_gini_financialisation_1990_2023` | supported | `marxian`, `post_keynesian` | `map_now_cross_school_supported` | broad associational panel; no duplicate flag |
| 9 | `cross_school_private_credit_growth_financialisation_1990_2023` | supported | `marxian`, `post_keynesian` | `map_now_cross_school_supported` | broad associational panel; no duplicate flag |
| 10 | `cross_school_tax_revenue_gini_redistribution_1990_2023` | supported | `social_democratic`, `market_socialist` | `map_now_cross_school_supported` | broad associational panel; no duplicate flag |
| 11 | `cross_school_tax_revenue_poverty_reduction_1990_2023` | supported | `social_democratic`, `market_socialist` | `map_now_cross_school_supported` | broad associational panel; no duplicate flag |
| 12 | `cross_school_electricity_access_child_mortality_1990_2023` | supported | `developmentalism`, `eco_socialist` | `map_now_cross_school_supported` | broad associational panel; no duplicate flag |
| 13 | `cross_school_renewables_growth_cost_tradeoff_1990_2023` | supported | `eco_socialist`, `classical_liberal` | `map_now_cross_school_supported` | broad associational panel; no duplicate flag |
| 14 | `cross_school_public_debt_growth_drag_1990_2023` | refuted | `marxian`, `mmt`, `post_keynesian` | `map_now_cross_school_refuted` | broad associational panel; no duplicate flag |
| 15 | `cross_school_gov_consumption_unemployment_stabiliser_1990_2023` | refuted | `post_keynesian`, `new_keynesian`, `social_democratic` | `map_now_cross_school_refuted` | broad associational panel; no duplicate flag |
| 16 | `cross_school_fiscal_balance_unemployment_austerity_1990_2023` | refuted | `post_keynesian`, `social_democratic` | `map_now_cross_school_refuted` | broad associational panel; no duplicate flag |
| 17 | `cross_school_tax_revenue_life_expectancy_social_capacity_1990_2023` | refuted | `social_democratic`, `new_keynesian` | `map_now_cross_school_refuted` | broad associational panel; no duplicate flag |
| 18 | `cross_school_tax_revenue_child_mortality_social_capacity_1990_2023` | refuted | `social_democratic`, `new_keynesian` | `map_now_cross_school_refuted` | broad associational panel; no duplicate flag |
| 19 | `cross_school_public_debt_unemployment_mmt_1990_2023` | refuted | `mmt`, `post_keynesian` | `map_now_cross_school_refuted` | broad associational panel; no duplicate flag |
| 20 | `cross_school_renewables_life_expectancy_ecosocial_1990_2023` | refuted | `eco_socialist`, `degrowth` | `map_now_cross_school_refuted` | broad associational panel; no duplicate flag |
| 21 | `cross_school_renewables_child_mortality_ecosocial_1990_2023` | refuted | `eco_socialist`, `degrowth` | `map_now_cross_school_refuted` | broad associational panel; no duplicate flag |
| 22 | `cross_school_fossil_electricity_child_mortality_ecosocial_1990_2023` | refuted | `eco_socialist`, `degrowth` | `map_now_cross_school_refuted` | broad associational panel; no duplicate flag |
| 23 | `cross_school_fossil_electricity_growth_development_tradeoff_1990_2023` | refuted | `eco_socialist`, `developmentalism` | `map_now_cross_school_refuted` | broad associational panel; no duplicate flag |
| 24 | `cross_school_energy_use_growth_degrowth_tradeoff_1990_2023` | refuted | `degrowth`, `eco_socialist` | `map_now_cross_school_refuted` | broad associational panel; no duplicate flag |
| 25 | `cross_school_fossil_electricity_life_expectancy_tradeoff_1990_2023` | refuted | `eco_socialist`, `degrowth` | `map_now_cross_school_refuted` | broad associational panel; no duplicate flag |

## Exact Claim Text Work

Use the generated hypothesis claim as the position claim stem, prefixed with the school name only when the local position style requires it. The claim stems are:

- `cross_school_efw_growth_market_order_1990_2023`: Higher broad economic freedom predicts faster real GDP per-capita growth.
- `cross_school_efw_private_investment_market_order_1990_2023`: Higher broad economic freedom predicts higher private-investment shares.
- `cross_school_sound_money_inflation_reduction_1990_2023`: Sound-money institutions predict lower inflation.
- `cross_school_rule_of_law_private_credit_depth_1996_2023`: Rule of law predicts deeper private credit intermediation.
- `cross_school_regulatory_quality_private_investment_1996_2023`: Regulatory quality predicts higher private-investment shares.
- `cross_school_trade_openness_growth_1990_2023`: Trade openness predicts faster real GDP per-capita growth.
- `cross_school_private_credit_manufacturing_financialisation_1990_2023`: Private-credit depth predicts manufacturing-share erosion, consistent with financialisation.
- `cross_school_private_credit_gini_financialisation_1990_2023`: Private-credit depth predicts higher income inequality.
- `cross_school_private_credit_growth_financialisation_1990_2023`: Private-credit depth does not reliably translate into faster GDP per-capita growth.
- `cross_school_tax_revenue_gini_redistribution_1990_2023`: Higher tax revenue shares predict lower inequality.
- `cross_school_tax_revenue_poverty_reduction_1990_2023`: Higher tax revenue shares predict lower extreme poverty.
- `cross_school_electricity_access_child_mortality_1990_2023`: Electricity access predicts lower child mortality.
- `cross_school_renewables_growth_cost_tradeoff_1990_2023`: Higher renewable-electricity shares predict faster GDP per-capita growth.
- `cross_school_public_debt_growth_drag_1990_2023`: Public debt is not necessarily growth-damaging in broad panels.
- `cross_school_gov_consumption_unemployment_stabiliser_1990_2023`: Higher government consumption predicts lower unemployment.
- `cross_school_fiscal_balance_unemployment_austerity_1990_2023`: Stronger fiscal balances predict higher unemployment if austerity is contractionary.
- `cross_school_tax_revenue_life_expectancy_social_capacity_1990_2023`: Higher tax revenue shares predict higher life expectancy through public capacity.
- `cross_school_tax_revenue_child_mortality_social_capacity_1990_2023`: Higher tax revenue shares predict lower child mortality.
- `cross_school_public_debt_unemployment_mmt_1990_2023`: Higher public debt is associated with lower unemployment if deficits accommodate demand.
- `cross_school_renewables_life_expectancy_ecosocial_1990_2023`: Higher renewable-electricity shares predict higher life expectancy.
- `cross_school_renewables_child_mortality_ecosocial_1990_2023`: Higher renewable-electricity shares predict lower child mortality.
- `cross_school_fossil_electricity_child_mortality_ecosocial_1990_2023`: Higher fossil-electricity shares predict worse child-mortality outcomes.
- `cross_school_fossil_electricity_growth_development_tradeoff_1990_2023`: Higher fossil-electricity shares predict faster GDP growth in development panels.
- `cross_school_energy_use_growth_degrowth_tradeoff_1990_2023`: Higher energy use per capita predicts faster GDP growth.
- `cross_school_fossil_electricity_life_expectancy_tradeoff_1990_2023`: Higher fossil-electricity shares predict lower life expectancy after controls.

## Deferred Items

### Cross-School Partial Direction QA

Do not map these 25 yet: `cross_school_regulation_employment_market_order_1990_2023`, `cross_school_trade_freedom_hightech_exports_1990_2023`, `cross_school_smaller_government_growth_1990_2023`, `cross_school_capital_openness_fdi_1990_2023`, `cross_school_gini_growth_underconsumption_1990_2023`, `cross_school_gini_employment_underconsumption_1990_2023`, `cross_school_gov_consumption_child_mortality_social_provision_1990_2023`, `cross_school_gov_consumption_life_expectancy_social_provision_1990_2023`, `cross_school_public_debt_inflation_mmt_1990_2023`, `cross_school_gov_consumption_growth_multiplier_1990_2023`, `cross_school_fiscal_balance_growth_austerity_1990_2023`, `cross_school_gov_consumption_private_investment_crowding_1990_2023`, `cross_school_fiscal_balance_private_investment_confidence_1990_2023`, `cross_school_government_effectiveness_hightech_developmental_1996_2023`, `cross_school_government_effectiveness_manufacturing_developmental_1996_2023`, `cross_school_government_effectiveness_fdi_developmental_1996_2023`, `cross_school_rule_of_law_hightech_institutional_1996_2023`, `cross_school_regulatory_quality_employment_institutional_1996_2023`, `cross_school_trade_openness_manufacturing_developmental_1990_2023`, `cross_school_fdi_hightech_developmental_1990_2023`, `cross_school_private_credit_hightech_developmental_1990_2023`, `cross_school_tertiary_hightech_human_capital_1990_2023`, `cross_school_government_effectiveness_growth_developmental_1996_2023`, `cross_school_energy_use_life_expectancy_degrowth_threshold_1990_2023`, `cross_school_electricity_access_growth_1990_2023`.

### Throughput Holds

- Keep all 18 `hold_duplicate_broad_panel_qa` items out of mapping until duplicate fingerprints are explained or repaired.
- Keep `tax_simplicity_disposable_income_growth` and `housing_tax_distortion_mobility` out until their broad proxies are narrowed.
- Treat the 28 `needs_position_claim_mapping` throughput items as a second-pass queue after this cross-school B1 wave, with priority for direct-measure upgrades already noted in the workplan: `economic_freedom_corruption_decline`, `regulatory_transparency_investment`, and the minimum-wage bite/QCEW pair.

## Validation Required After Mapping

1. Run scope alignment validation.
2. Run link reciprocity validation.
3. Re-run the throughput conversion audit.
4. Recompute scoreboard only after zero reciprocity errors.
5. Compare the scoreboard against `engine/audits/scoreboard_prediction_outcome_audit_2026-05-12_after_mapping_wave1.md`; expected movement should be modest because all selected items are associational and should be q-weighted accordingly.
