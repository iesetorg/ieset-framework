# Scoreboard Conversion Workplan

Date: 2026-05-12

Purpose: turn the new monthly-throughput verdict inventory into scoreboard evidence without letting weak, duplicated, broad-panel results over-weight any school.

Source audit: `engine/audits/throughput_scoreboard_conversion_2026-05-12.md`

## Current Conversion Gate

Reviewed: 129 hypotheses from the 2026-05-12 kickoff plus Batches 02-04.

| bucket | count | action |
| --- | ---: | --- |
| `scoreboard_ready_existing_mapping` | 31 | Eligible for next scoreboard recompute. |
| `needs_position_claim_mapping` | 28 | Needs explicit school claim text, prediction, polarity, and reciprocal `covers_claims`. |
| `hold_interpretation_qa` | 29 | Do not score until partial direction/ambiguous effect is clarified. |
| `hold_duplicate_broad_panel_qa` | 18 | Do not score until hypothesis-specific evidence is upgraded or duplicate fingerprint is explained. |
| `hold_broad_panel_upgrade` | 2 | Do not score until broad proxy is sharpened. |
| `repair_data_or_design` | 21 | Not verdict-bearing; repair data/model first. |

## Repairs Applied

Two low-risk reciprocal mappings were fixed because the position-side links already existed:

- `argentina_cepo_lift_2015_fx_inflation_reserves`
  - position: `classical_liberal`, claim 65
  - prediction: supported
  - polarity: aligned
  - evidence caveat: compact event-window evidence, not broad structural proof
- `argentina_paso_2019_fx_reserves_inflation_base_money_lag`
  - position: `chicago_monetarism`, claim 66
  - prediction: supported
  - polarity: aligned
  - evidence caveat: compact event-window evidence, not broad structural proof

Mapping Wave 1 then added 32 reviewed reciprocal links across 11 previously-unmapped hypotheses:

- `business_dynamism_frontier_income_growth`
- `platform_competition_dissipates_monopoly_rent`
- `price_controls_food_output_decline_panel`
- `spectrum_auction_vs_administrative_allocation_telecom`
- `banking_crisis_schularick_taylor_credit_boom_panel_post1980`
- `banking_crisis_laeven_valencia_predictors_panel`
- `debt_overhang_private_investment_30yr`
- `bank_state_ownership_credit_misallocation`
- `venture_capital_market_depth_innovation`
- `gm_crop_adoption_yield_convergence`
- `china_renewables_global_learning_curve_spillover`

Validation after repair:

- `validate_scope_alignment.py`: 2313 pass, 0 errors.
- `validate_link_reciprocity.py --summary`: 2319 position-side links, 2319 hypothesis-side coverages, 0 errors, 0 warnings.

## Scoreboard-Ready Inventory

These can be counted in the next scoreboard recompute because they already have mappings and are not held by the conversion QA gate:

- `market_order_capital_account_openness_gdp_pc_growth_panel`
- `market_order_capital_account_openness_private_investment_share_panel`
- `market_order_fiscal_balance_gdp_pc_growth_panel`
- `market_order_fiscal_balance_private_investment_share_panel`
- `market_order_fiscal_balance_gross_savings_share_panel`
- `market_order_fiscal_balance_private_credit_depth_panel`
- `market_order_public_debt_private_investment_share_panel`
- `market_order_government_consumption_gdp_pc_growth_panel`
- `market_order_government_consumption_gross_savings_share_panel`
- `strong_union_labour_law_youth_unemployment_south_europe`
- `firm_entry_rate_long_run_productivity`
- `bukele_fiscal_trajectory_tax_cuts_imf_2019_2024`
- `frontier_income_volatility_state_allocation`
- `absolute_decoupling_global_material_throughput`
- `albania_growth_health_services_shift_1990_2023`
- `argentina_cepo_lift_2015_fx_inflation_reserves`
- `argentina_fx_obligation_inflation_mechanism`
- `argentina_paso_2019_fx_reserves_inflation_base_money_lag`
- `argentina_peronism_recurring_fiscal_inflation_cycle_1945_2023`
- `armenia_growth_health_services_shift_1990_2023`
- `bank_state_ownership_credit_misallocation`
- `banking_crisis_laeven_valencia_predictors_panel`
- `banking_crisis_schularick_taylor_credit_boom_panel_post1980`
- `business_dynamism_frontier_income_growth`
- `china_renewables_global_learning_curve_spillover`
- `debt_overhang_private_investment_30yr`
- `gm_crop_adoption_yield_convergence`
- `platform_competition_dissipates_monopoly_rent`
- `price_controls_food_output_decline_panel`
- `spectrum_auction_vs_administrative_allocation_telecom`
- `venture_capital_market_depth_innovation`

## Mapping Wave 1 Scoreboard Movement

Output: `engine/audits/scoreboard_prediction_outcome_audit_2026-05-12_after_mapping_wave1.md`

| school | q-net after | q-net change | raw-net change | tested change |
| --- | ---: | ---: | ---: | ---: |
| `chicago_monetarism` | 20.8 | +1.2 | +1.5 | +2 |
| `austrian` | 16.2 | +1.0 | +1.0 | +4 |
| `developmentalism` | 11.0 | +1.0 | +2.0 | +2 |
| `mmt` | -1.1 | +1.0 | +2.0 | +2 |
| `post_keynesian` | -1.8 | +1.0 | +2.0 | +2 |
| `marxian` | -2.9 | +1.0 | +2.0 | +2 |
| `democratic_socialist` | -3.4 | +1.0 | +2.0 | +2 |
| `ordoliberal` | 16.5 | -0.5 | -1.0 | +5 |
| `classical_liberal` | 15.2 | -0.5 | -2.0 | +8 |

## Mapping Queue

The 36 unmapped verdict-bearing hypotheses should be mapped in small reviewed waves. Recommended first wave:

- `us_qcew_county_food_service_minimum_wage_panel`
- `china_renewables_global_learning_curve_spillover`
- `business_dynamism_frontier_income_growth`
- `platform_competition_dissipates_monopoly_rent`
- `price_controls_food_output_decline_panel`
- `spectrum_auction_vs_administrative_allocation_telecom`
- `banking_crisis_schularick_taylor_credit_boom_panel_post1980`
- `bank_state_ownership_credit_misallocation`
- `debt_overhang_private_investment_30yr`
- `gm_crop_adoption_yield_convergence`
- `venture_capital_market_depth_innovation`
- `banking_crisis_laeven_valencia_predictors_panel`

Mapping rule:

1. Add or reuse a position claim only when the school-specific claim text matches the hypothesis scope.
2. Set `school_prediction` before looking at scoreboard effect.
3. Set `claim_polarity` by reading both the position claim and hypothesis claim.
4. Add reciprocal `covers_claims` in the hypothesis YAML.
5. Run scope and reciprocity validations before recomputing scoreboard.

## Duplicate Broad-Panel Upgrade Queue

Detailed plan: `engine/audits/duplicate_broad_panel_upgrade_plan_2026-05-12.md`

These are held because multiple hypotheses emit identical or near-identical coefficient fingerprints from broad associational panels. They must not be mapped for score weight until upgraded:

- `price_signal_integrity_qol_panel`
- `intervention_reversal_qol_loss_1980_2024`
- `crony_capitalism_not_market_freedom`
- `market_institution_duration_qol_persistence`
- `qol_anomaly_weight_broad_scope_test`
- `occupational_licensing_income_mobility`
- `market_reform_inflation_adjusted_wages`
- `market_governance_qol_broad_scope`
- `public_procurement_innovation_conditions`
- `intervention_intensity_qol_volatility_1970_2024`
- `procurement_competition_corruption`
- `labor_reform_real_wage_growth`
- `campaign_favoritism_subsidy_allocation`
- `licensing_discretion_bribery`
- `CBDC_design_privacy_tradeoff`
- `active_labour_market_policy_conditionality_works`
- `agricultural_export_ban_price_instability`
- `agricultural_trade_liberalisation_food_security`
- `apprenticeship_employer_chamber_quality`

Upgrade rule:

1. Replace generic broad proxy with a hypothesis-specific treatment.
2. Replace reused outcome with a direct outcome matching the claim.
3. Require a unique estimate fingerprint or a documented reason why a shared panel is valid.
4. Keep `evidence_type: associational` unless a stronger design is genuinely registered.
5. Only then allow claim mapping or scoreboard conversion.

Priority decisions from Lane 2:

- Completed direct upgrade: `regulatory_transparency_investment` now uses OECD PMR regulatory-process measures and WDI investment share; verdict moved from duplicate broad-panel supported to direct-measure partial, and it now sits in `needs_position_claim_mapping` rather than duplicate hold.
- Completed direct upgrade: `economic_freedom_corruption_decline` now uses V-Dem rule of law and V-Dem corruption outcomes; verdict remains supported, and it now sits in `needs_position_claim_mapping` rather than duplicate hold.
- Near-term upgrade candidates: none remain from the local-data-ready duplicate set.
- Data-gap upgrade candidate: `occupational_licensing_income_mobility`.
- Do not score directly: `market_governance_qol_broad_scope`, `qol_anomaly_weight_broad_scope_test`.
- Remaining duplicate groups need the same review pattern: if the data do not directly measure the claim, repair the hypothesis before mapping it.

## Broad Proxy Upgrade Queue

- `tax_simplicity_disposable_income_growth`
- `housing_tax_distortion_mobility`

These are not duplicate-fingerprint cases, but their current evidence is too broad relative to the claim. They need sharper treatment/outcome definitions before scoreboard conversion.

## Interpretation QA Queue

Partial verdicts with direction-inconclusive, zero-effect, or ambiguous-claim language should stay out of scoreboard movement unless converted to neutral partial with explicit methodology notes. This prevents partials from quietly pushing schools up or down.

## Next Work Slice

1. Map the first 12 mapping candidates in a reviewed wave.
2. Upgrade 5 duplicate broad-panel hypotheses by replacing generic treatments/outcomes.
3. Re-run conversion audit.
4. Re-run scope and reciprocity validation.
5. Only then recompute scoreboard.
