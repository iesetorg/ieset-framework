# School Coverage Balance Audit

Generated: 2026-10-11

## Methodology Gate

- This is a coverage and repair queue, not a school ranking or a change to verdicts and scores.
- The unit is unique existing hypothesis IDs linked from a school's falsifiable claims.
- The scoreboard itself counts prediction rows. Its claim-row totals are also reported so duplicate links do not create a false audit mismatch.
- A tested link must pass the current evidence-tier public gate and school-score gate and have a scored verdict. A visible run file alone does not qualify.
- A school forecast scores only when its exact claim and reciprocal prediction were committed before that hypothesis's first run. Later mappings remain visible as descriptive links.
- A directional scored link has a school forecast and a non-neutral support, refutation or directional partial outcome; a `mixed` forecast and neutral partial do not qualify.
- Archived runs whose spec and result first appeared in one commit cannot become preregistered by relabeling; they require a genuinely prospective test.
- V1 balanced means at least `100` unique linked hypotheses and `60` score-eligible tested hypotheses.
- Stretch balanced means at least `125` unique linked hypotheses and `80` unique tested hypotheses.

## Summary

- Ranked schools tracked: 16 (benchmark controls excluded: 1)
- V1 balanced schools: 0
- Under-covered schools: 16
- Unique linked hypothesis range: 283-354
- Unique score-eligible tested hypothesis range: 0-53
- Unique directional scored hypothesis range: 0-18
- Total gap to 200 directional scored links per school: 3136
- Theoretical minimum new directional claims even if every existing directional link passes: 267
- V1 linked deficit remaining: 0
- V1 tested deficit remaining: 786

## V1 Coverage Queue

| school | linked IDs | public IDs | eligible IDs | tested IDs | scoreboard tested claims | directional scored IDs | pending IDs | link gap | test gap | status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `marxist_leninist` | 283 | 18 | 17 | 0 | 0 | 0 | 283 | 0 | 60 | under_covered |
| `post_keynesian` | 285 | 17 | 16 | 0 | 0 | 0 | 285 | 0 | 60 | under_covered |
| `new_keynesian` | 286 | 19 | 18 | 0 | 0 | 0 | 286 | 0 | 60 | under_covered |
| `democratic_socialist` | 287 | 18 | 17 | 0 | 0 | 0 | 287 | 0 | 60 | under_covered |
| `degrowth` | 289 | 20 | 19 | 0 | 0 | 0 | 289 | 0 | 60 | under_covered |
| `marxian` | 290 | 21 | 20 | 0 | 0 | 0 | 290 | 0 | 60 | under_covered |
| `eco_socialist` | 292 | 16 | 15 | 0 | 0 | 0 | 292 | 0 | 60 | under_covered |
| `developmentalism` | 301 | 21 | 20 | 0 | 0 | 0 | 301 | 0 | 60 | under_covered |
| `mmt` | 286 | 21 | 20 | 1 | 1 | 1 | 285 | 0 | 59 | under_covered |
| `market_socialist` | 288 | 21 | 20 | 1 | 1 | 1 | 287 | 0 | 59 | under_covered |
| `social_democratic` | 301 | 20 | 19 | 1 | 1 | 1 | 300 | 0 | 59 | under_covered |
| `institutionalism` | 293 | 33 | 32 | 12 | 12 | 1 | 281 | 0 | 48 | under_covered |
| `chicago_monetarism` | 300 | 35 | 34 | 14 | 14 | 9 | 286 | 0 | 46 | under_covered |
| `austrian` | 296 | 63 | 62 | 40 | 40 | 16 | 256 | 0 | 20 | under_covered |
| `ordoliberal` | 319 | 76 | 75 | 52 | 52 | 17 | 267 | 0 | 8 | under_covered |
| `classical_liberal` | 354 | 84 | 83 | 53 | 53 | 18 | 301 | 0 | 7 | under_covered |

## Path to 200 Directional Scored Tests per School

The gap is a forecast-score coverage target. It is not strict attribution-aware school credit; second-order measurement gates remain separate.
Blocker counts overlap when an archived result fails more than one gate. The full hypothesis-by-hypothesis queue and exact reasons are in the paired CSV.

| school | directional linked | scored | gap to 200 | minimum new directional claims | archived links | top blockers |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `marxist_leninist` | 164 | 0 | 200 | 36 | 265 | registration_legacy_same_commit (144), estimator_floor_failed (20), non_result_verdict (13) |
| `post_keynesian` | 254 | 0 | 200 | 0 | 268 | registration_legacy_same_commit (227), estimator_floor_failed (31), school_prediction_not_pre_run (15) |
| `new_keynesian` | 90 | 0 | 200 | 110 | 267 | registration_legacy_same_commit (83), estimator_floor_failed (6), non_result_verdict (5) |
| `democratic_socialist` | 266 | 0 | 200 | 0 | 269 | registration_legacy_same_commit (242), estimator_floor_failed (31), school_prediction_not_pre_run (14) |
| `degrowth` | 151 | 0 | 200 | 49 | 269 | registration_legacy_same_commit (149), estimator_floor_failed (20), non_result_verdict (8) |
| `marxian` | 219 | 0 | 200 | 0 | 269 | registration_legacy_same_commit (196), estimator_floor_failed (25), school_prediction_not_pre_run (19) |
| `eco_socialist` | 230 | 0 | 200 | 0 | 276 | registration_legacy_same_commit (214), estimator_floor_failed (29), non_result_verdict (13) |
| `developmentalism` | 169 | 0 | 200 | 31 | 280 | registration_legacy_same_commit (149), estimator_floor_failed (14), school_prediction_not_pre_run (12) |
| `mmt` | 206 | 1 | 199 | 0 | 265 | registration_legacy_same_commit (183), estimator_floor_failed (22), school_prediction_not_pre_run (18) |
| `market_socialist` | 255 | 1 | 199 | 0 | 267 | registration_legacy_same_commit (232), estimator_floor_failed (28), school_prediction_not_pre_run (18) |
| `social_democratic` | 278 | 1 | 199 | 0 | 281 | registration_legacy_same_commit (249), estimator_floor_failed (33), school_prediction_not_pre_run (12) |
| `institutionalism` | 159 | 1 | 199 | 41 | 260 | registration_legacy_same_commit (123), estimator_floor_failed (20), school_prediction_not_pre_run (13) |
| `chicago_monetarism` | 233 | 9 | 191 | 0 | 265 | registration_legacy_same_commit (192), estimator_floor_failed (26), school_prediction_not_pre_run (15) |
| `austrian` | 243 | 16 | 184 | 0 | 233 | registration_legacy_same_commit (175), neutral_result (24), estimator_floor_failed (23) |
| `ordoliberal` | 258 | 17 | 183 | 0 | 243 | registration_legacy_same_commit (171), neutral_result (35), estimator_floor_failed (26) |
| `classical_liberal` | 308 | 18 | 182 | 0 | 270 | registration_legacy_same_commit (211), neutral_result (35), estimator_floor_failed (30) |

## First Existing Candidates by School

This is a triage order, not permission to reclassify results. A verified preregistration with another blocker appears first; older same-commit studies require new frozen specifications and genuinely new data or holdouts.

### `marxist_leninist`

- `australia_hawke_keating_reform_long_run` (regulatory.trade_openness): external_integrity_quarantine.
- `canada_market_liberalisation_vs_state_industry_1988_2024` (regulatory.trade_openness): estimator_floor_failed.
- `financial_liberalisation_crisis_risk` (regulatory.financial_deregulation): school_prediction_not_pre_run.
- `firm_entry_rate_long_run_productivity` (regulatory.product_market_competition): external_integrity_quarantine.
- `frontier_income_volatility_state_allocation` (regulatory.trade_openness): external_integrity_quarantine.
- `government_consumption_share_tfp` (regulatory.trade_openness): external_integrity_quarantine.
- `market_order_government_spending_employment_rate_panel` (fiscal.spending_level): school_prediction_not_pre_run.
- `market_order_government_spending_gdp_pc_growth_panel` (fiscal.spending_level): school_prediction_not_pre_run.

### `post_keynesian`

- `active_labour_market_policy_conditionality_works` (regulatory.labour_market_flexibility): estimator_floor_failed.
- `apprenticeship_employer_chamber_quality` (regulatory.labour_market_flexibility): estimator_floor_failed.
- `australia_hawke_keating_reform_long_run` (regulatory.trade_openness): external_integrity_quarantine.
- `bis_credit_gap_current_account_twin_deficit_risk` (unclassified): school_prediction_not_pre_run.
- `canada_market_liberalisation_vs_state_industry_1988_2024` (regulatory.trade_openness): estimator_floor_failed.
- `eurostat_electricity_price_inflation_pass_through` (unclassified): school_prediction_not_pre_run.
- `financial_liberalisation_crisis_risk` (regulatory.financial_deregulation): school_prediction_not_pre_run.
- `firm_entry_rate_long_run_productivity` (regulatory.product_market_competition): external_integrity_quarantine.

### `new_keynesian`

- `asia_japan_abenomics_retrospective_2013_2023` (monetary.monetary_expansion_direction): school_prediction_not_pre_run.
- `contract_enforcement_fdi_productivity_spillovers` (institutional.rule_of_law): external_integrity_quarantine.
- `corruption_state_allocation_growth_interaction` (institutional.rule_of_law): external_integrity_quarantine.
- `eurostat_electricity_price_inflation_pass_through` (unclassified): school_prediction_not_pre_run.
- `industrial_policy_high_governance_success` (regulatory.trade_openness): external_integrity_quarantine.
- `judicial_independence_growth_persistence` (institutional.judicial_independence): estimator_floor_failed.
- `labour_flexibility_security_complement` (regulatory.labour_market_flexibility): estimator_floor_failed.
- `agricultural_productivity_poverty_reduction_panel` (unclassified): registration_legacy_same_commit.

### `democratic_socialist`

- `australia_hawke_keating_reform_long_run` (regulatory.trade_openness): external_integrity_quarantine.
- `canada_market_liberalisation_vs_state_industry_1988_2024` (regulatory.trade_openness): estimator_floor_failed.
- `financial_liberalisation_crisis_risk` (regulatory.financial_deregulation): school_prediction_not_pre_run.
- `firm_entry_rate_long_run_productivity` (regulatory.product_market_competition): external_integrity_quarantine.
- `frontier_income_volatility_state_allocation` (regulatory.trade_openness): external_integrity_quarantine.
- `government_consumption_share_tfp` (regulatory.trade_openness): external_integrity_quarantine.
- `market_order_government_spending_employment_rate_panel` (fiscal.spending_level): school_prediction_not_pre_run.
- `market_order_government_spending_gdp_pc_growth_panel` (fiscal.spending_level): school_prediction_not_pre_run.

### `degrowth`

- `natural_monopoly_private_failure` (institutional.property_rights): school_prediction_not_pre_run.
- `absolute_decoupling_global_material_throughput` (regulatory.trade_openness): registration_legacy_same_commit.
- `argentina_peronism_recurring_fiscal_inflation_cycle_1945_2023` (monetary.monetary_expansion_direction): registration_legacy_same_commit.
- `asian_convergence_vs_western_stagnation_2000_2023` (regulatory.product_market_competition): registration_legacy_same_commit.
- `bis_credit_gap_house_price_unemployment_lag_panel` (unclassified): registration_legacy_same_commit.
- `bis_house_price_growth_consumption_squeeze_panel` (unclassified): registration_legacy_same_commit.
- `bis_household_dsr_policy_rate_consumption_slowdown_panel` (unclassified): registration_legacy_same_commit.
- `bis_low_policy_rate_credit_gap_asset_cycle_panel` (unclassified): registration_legacy_same_commit.

### `marxian`

- `bis_credit_gap_current_account_twin_deficit_risk` (unclassified): school_prediction_not_pre_run.
- `financial_liberalisation_crisis_risk` (regulatory.financial_deregulation): school_prediction_not_pre_run.
- `market_order_government_spending_employment_rate_panel` (fiscal.spending_level): school_prediction_not_pre_run.
- `market_order_government_spending_gdp_pc_growth_panel` (fiscal.spending_level): school_prediction_not_pre_run.
- `market_order_government_spending_investment_share_panel` (fiscal.spending_level): school_prediction_not_pre_run.
- `market_order_government_spending_private_credit_depth_panel` (fiscal.spending_level): school_prediction_not_pre_run.
- `market_order_sound_money_employment_rate_panel` (monetary.monetary_expansion_direction): school_prediction_not_pre_run.
- `market_order_sound_money_gdp_pc_growth_panel` (monetary.monetary_expansion_direction): school_prediction_not_pre_run.

### `eco_socialist`

- `carbon_tax_revenue_neutral_double_dividend` (regulatory.environmental_stringency): estimator_floor_failed.
- `financial_liberalisation_crisis_risk` (regulatory.financial_deregulation): school_prediction_not_pre_run.
- `market_order_government_spending_employment_rate_panel` (fiscal.spending_level): school_prediction_not_pre_run.
- `market_order_government_spending_gdp_pc_growth_panel` (fiscal.spending_level): school_prediction_not_pre_run.
- `market_order_government_spending_investment_share_panel` (fiscal.spending_level): school_prediction_not_pre_run.
- `market_order_government_spending_private_credit_depth_panel` (fiscal.spending_level): school_prediction_not_pre_run.
- `market_order_tax_burden_gdp_pc_growth_panel` (fiscal.tax_progressivity): school_prediction_not_pre_run.
- `market_order_tax_burden_investment_share_panel` (fiscal.tax_progressivity): school_prediction_not_pre_run.

### `developmentalism`

- `africa_botswana_diamond_dependency_post_2014` (fiscal.sectoral_subsidy): school_prediction_not_pre_run.
- `africa_ethiopia_gerd_economic_effect_2011_2024` (fiscal.sectoral_subsidy): school_prediction_not_pre_run.
- `africa_ssa_post_covid_recovery_divergence_2020_2024` (monetary.monetary_expansion_direction): external_integrity_quarantine.
- `asia_bangladesh_apparel_growth_1985_2024` (regulatory.trade_openness): school_prediction_not_pre_run.
- `asia_pakistan_imf_programme_cycle_1988_2024` (monetary.monetary_expansion_direction): school_prediction_not_pre_run.
- `contract_enforcement_fdi_productivity_spillovers` (institutional.rule_of_law): external_integrity_quarantine.
- `corruption_state_allocation_growth_interaction` (institutional.rule_of_law): external_integrity_quarantine.
- `india_extra_aadhaar_upi_productivity` (institutional.property_rights): school_prediction_not_pre_run.

### `mmt`

- `financial_liberalisation_crisis_risk` (regulatory.financial_deregulation): school_prediction_not_pre_run.
- `market_order_government_spending_employment_rate_panel` (fiscal.spending_level): school_prediction_not_pre_run.
- `market_order_government_spending_gdp_pc_growth_panel` (fiscal.spending_level): school_prediction_not_pre_run.
- `market_order_government_spending_investment_share_panel` (fiscal.spending_level): school_prediction_not_pre_run.
- `market_order_government_spending_private_credit_depth_panel` (fiscal.spending_level): school_prediction_not_pre_run.
- `market_order_sound_money_employment_rate_panel` (monetary.monetary_expansion_direction): school_prediction_not_pre_run.
- `market_order_sound_money_gdp_pc_growth_panel` (monetary.monetary_expansion_direction): school_prediction_not_pre_run.
- `market_order_sound_money_investment_share_panel` (monetary.monetary_expansion_direction): school_prediction_not_pre_run.

### `market_socialist`

- `financial_liberalisation_crisis_risk` (regulatory.financial_deregulation): school_prediction_not_pre_run.
- `market_order_government_spending_employment_rate_panel` (fiscal.spending_level): school_prediction_not_pre_run.
- `market_order_government_spending_gdp_pc_growth_panel` (fiscal.spending_level): school_prediction_not_pre_run.
- `market_order_government_spending_investment_share_panel` (fiscal.spending_level): school_prediction_not_pre_run.
- `market_order_government_spending_private_credit_depth_panel` (fiscal.spending_level): school_prediction_not_pre_run.
- `market_order_sound_money_employment_rate_panel` (monetary.monetary_expansion_direction): school_prediction_not_pre_run.
- `market_order_sound_money_gdp_pc_growth_panel` (monetary.monetary_expansion_direction): school_prediction_not_pre_run.
- `market_order_sound_money_investment_share_panel` (monetary.monetary_expansion_direction): school_prediction_not_pre_run.

### `social_democratic`

- `africa_ethiopia_tigray_war_economic_collapse_2020_2022` (monetary.monetary_expansion_direction): school_prediction_not_pre_run.
- `africa_rwanda_post_genocide_growth_model_1995_2024` (fiscal.transfer_expansion): school_prediction_not_pre_run.
- `australia_hawke_keating_reform_long_run` (regulatory.trade_openness): external_integrity_quarantine.
- `australia_tobacco_excise_punitive_vs_harm_reduction_comparators` (fiscal.transfer_expansion): school_prediction_not_pre_run.
- `canada_market_liberalisation_vs_state_industry_1988_2024` (regulatory.trade_openness): estimator_floor_failed.
- `contract_enforcement_fdi_productivity_spillovers` (institutional.rule_of_law): external_integrity_quarantine.
- `corruption_state_allocation_growth_interaction` (institutional.rule_of_law): external_integrity_quarantine.
- `firm_entry_rate_long_run_productivity` (regulatory.product_market_competition): external_integrity_quarantine.

### `institutionalism`

- `africa_botswana_diamond_dependency_post_2014` (fiscal.sectoral_subsidy): school_prediction_not_pre_run.
- `africa_ethiopia_tigray_war_economic_collapse_2020_2022` (monetary.monetary_expansion_direction): school_prediction_not_pre_run.
- `africa_rwanda_post_genocide_growth_model_1995_2024` (fiscal.transfer_expansion): school_prediction_not_pre_run.
- `asia_pakistan_imf_programme_cycle_1988_2024` (monetary.monetary_expansion_direction): school_prediction_not_pre_run.
- `bankruptcy_law_efficiency_capital_reallocation` (regulatory.trade_openness): estimator_floor_failed.
- `chile_market_reform_long_horizon_with_democracy` (regulatory.trade_openness): school_prediction_not_pre_run.
- `constitutional_fiscal_rules_growth_stability` (regulatory.trade_openness): estimator_floor_failed.
- `contract_enforcement_fdi_productivity_spillovers` (institutional.rule_of_law): external_integrity_quarantine.

### `chicago_monetarism`

- `argentina_fx_obligation_inflation_mechanism` (monetary.monetary_expansion_direction): school_prediction_not_pre_run.
- `asia_japan_abenomics_retrospective_2013_2023` (monetary.monetary_expansion_direction): school_prediction_not_pre_run.
- `australia_hawke_keating_reform_long_run` (regulatory.trade_openness): external_integrity_quarantine.
- `canada_market_liberalisation_vs_state_industry_1988_2024` (regulatory.trade_openness): estimator_floor_failed.
- `capital_gains_tax_cut_investment_response_panel` (fiscal.tax_capital): school_prediction_not_pre_run.
- `debt_overhang_private_investment_30yr` (monetary.monetary_expansion_direction): school_prediction_not_pre_run.
- `firm_entry_rate_long_run_productivity` (regulatory.product_market_competition): external_integrity_quarantine.
- `fiscal_consolidation_credibility_growth` (fiscal.spending_level): school_prediction_not_pre_run.

### `austrian`

- `australia_hawke_keating_reform_long_run` (regulatory.trade_openness): external_integrity_quarantine.
- `business_dynamism_frontier_income_growth` (regulatory.product_market_competition): school_prediction_not_pre_run.
- `canada_market_liberalisation_vs_state_industry_1988_2024` (regulatory.trade_openness): estimator_floor_failed.
- `debt_overhang_private_investment_30yr` (monetary.monetary_expansion_direction): school_prediction_not_pre_run.
- `firm_entry_rate_long_run_productivity` (regulatory.product_market_competition): external_integrity_quarantine.
- `frontier_income_volatility_state_allocation` (regulatory.trade_openness): external_integrity_quarantine.
- `government_consumption_share_tfp` (regulatory.trade_openness): external_integrity_quarantine.
- `industrial_policy_high_governance_success` (regulatory.trade_openness): external_integrity_quarantine.

### `ordoliberal`

- `australia_hawke_keating_reform_long_run` (regulatory.trade_openness): external_integrity_quarantine.
- `bankruptcy_law_efficiency_capital_reallocation` (regulatory.trade_openness): estimator_floor_failed.
- `business_dynamism_frontier_income_growth` (regulatory.product_market_competition): school_prediction_not_pre_run.
- `canada_market_liberalisation_vs_state_industry_1988_2024` (regulatory.trade_openness): estimator_floor_failed.
- `chile_market_reform_long_horizon_with_democracy` (regulatory.trade_openness): school_prediction_not_pre_run.
- `constitutional_fiscal_rules_growth_stability` (regulatory.trade_openness): estimator_floor_failed.
- `contract_enforcement_fdi_productivity_spillovers` (institutional.rule_of_law): external_integrity_quarantine.
- `corruption_state_allocation_growth_interaction` (institutional.rule_of_law): external_integrity_quarantine.

### `classical_liberal`

- `asia_bangladesh_apparel_growth_1985_2024` (regulatory.trade_openness): school_prediction_not_pre_run.
- `australia_hawke_keating_reform_long_run` (regulatory.trade_openness): external_integrity_quarantine.
- `australia_tobacco_excise_punitive_vs_harm_reduction_comparators` (fiscal.transfer_expansion): school_prediction_not_pre_run.
- `bankruptcy_law_efficiency_capital_reallocation` (regulatory.trade_openness): estimator_floor_failed.
- `business_dynamism_frontier_income_growth` (regulatory.product_market_competition): school_prediction_not_pre_run.
- `canada_market_liberalisation_vs_state_industry_1988_2024` (regulatory.trade_openness): estimator_floor_failed.
- `capital_gains_tax_cut_investment_response_panel` (fiscal.tax_capital): school_prediction_not_pre_run.
- `chile_market_reform_long_horizon_with_democracy` (regulatory.trade_openness): school_prediction_not_pre_run.

## Research Sequence

1. Audit each school-specific forecast, mechanism and polarity against the original claim before a test is designed. Keep `mixed` forecasts neutral unless a new precommitted claim is authored.
2. Repair verified, genuinely runnable archival candidates only when the recorded data and estimator support the claim. Preserve failed and inconclusive results.
3. For legacy same-commit studies, freeze a new specification before a genuinely new source vintage or holdout test. Keep the older result archived.
4. Add new school-distinctive directional hypotheses where existing directional capacity is below target. Require an explicit falsifier, data source, scope, comparator and multiple-testing family.
5. Rebuild the evidence ledger, school audit and scoreboard, then verify strict second-order gates independently before making a school-level inference.
