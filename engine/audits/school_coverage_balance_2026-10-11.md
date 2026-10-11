# School Coverage Balance Audit

Generated: 2026-10-11

## Methodology Gate

- This is a coverage and repair queue, not a school ranking or a change to verdicts and scores.
- The unit is unique existing hypothesis IDs linked from a school's falsifiable claims.
- The scoreboard itself counts prediction rows. Its claim-row totals are also reported so duplicate links do not create a false audit mismatch.
- A tested link must pass the current evidence-tier public gate and school-score gate and have a scored verdict. A visible run file alone does not qualify.
- A directional scored link has a school forecast and a non-neutral support, refutation or directional partial outcome; a `mixed` forecast and neutral partial do not qualify.
- Archived runs whose spec and result first appeared in one commit cannot become preregistered by relabeling; they require a genuinely prospective test.
- V1 balanced means at least `100` unique linked hypotheses and `60` score-eligible tested hypotheses.
- Stretch balanced means at least `125` unique linked hypotheses and `80` unique tested hypotheses.

## Summary

- Ranked schools tracked: 16 (benchmark controls excluded: 1)
- V1 balanced schools: 3
- Under-covered schools: 13
- Unique linked hypothesis range: 283-354
- Unique score-eligible tested hypothesis range: 15-83
- Unique directional scored hypothesis range: 1-47
- Total gap to 200 directional scored links per school: 2929
- Theoretical minimum new directional claims even if every existing directional link passes: 268
- V1 linked deficit remaining: 0
- V1 tested deficit remaining: 513

## V1 Coverage Queue

| school | linked IDs | public IDs | eligible IDs | tested IDs | scoreboard tested claims | directional scored IDs | pending IDs | link gap | test gap | status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `eco_socialist` | 292 | 16 | 15 | 15 | 15 | 9 | 277 | 0 | 45 | under_covered |
| `post_keynesian` | 285 | 17 | 16 | 16 | 16 | 13 | 269 | 0 | 44 | under_covered |
| `marxist_leninist` | 283 | 18 | 17 | 17 | 17 | 9 | 266 | 0 | 43 | under_covered |
| `democratic_socialist` | 287 | 18 | 17 | 17 | 17 | 12 | 270 | 0 | 43 | under_covered |
| `new_keynesian` | 286 | 19 | 18 | 18 | 18 | 2 | 268 | 0 | 42 | under_covered |
| `degrowth` | 288 | 20 | 19 | 19 | 19 | 1 | 269 | 0 | 41 | under_covered |
| `social_democratic` | 300 | 20 | 19 | 19 | 20 | 13 | 281 | 0 | 41 | under_covered |
| `mmt` | 286 | 21 | 20 | 20 | 20 | 15 | 266 | 0 | 40 | under_covered |
| `market_socialist` | 288 | 21 | 20 | 20 | 20 | 15 | 268 | 0 | 40 | under_covered |
| `marxian` | 290 | 21 | 20 | 20 | 20 | 15 | 270 | 0 | 40 | under_covered |
| `developmentalism` | 301 | 21 | 20 | 20 | 20 | 12 | 281 | 0 | 40 | under_covered |
| `institutionalism` | 293 | 33 | 32 | 32 | 32 | 14 | 261 | 0 | 28 | under_covered |
| `chicago_monetarism` | 300 | 35 | 34 | 34 | 34 | 24 | 266 | 0 | 26 | under_covered |
| `austrian` | 296 | 63 | 62 | 62 | 62 | 34 | 234 | 0 | 0 | balanced_v1 |
| `ordoliberal` | 319 | 76 | 75 | 75 | 75 | 36 | 244 | 0 | 0 | balanced_v1 |
| `classical_liberal` | 354 | 84 | 83 | 83 | 83 | 47 | 271 | 0 | 0 | balanced_v1 |

## Path to 200 Directional Scored Tests per School

The gap is a forecast-score coverage target. It is not strict attribution-aware school credit; second-order measurement gates remain separate.
Blocker counts overlap when an archived result fails more than one gate. The full hypothesis-by-hypothesis queue and exact reasons are in the paired CSV.

| school | directional linked | scored | gap to 200 | minimum new directional claims | archived links | top blockers |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `eco_socialist` | 230 | 9 | 191 | 0 | 276 | registration_legacy_same_commit (214), estimator_floor_failed (29), non_result_verdict (13) |
| `post_keynesian` | 254 | 13 | 187 | 0 | 268 | registration_legacy_same_commit (227), estimator_floor_failed (31), non_result_verdict (10) |
| `marxist_leninist` | 164 | 9 | 191 | 36 | 265 | registration_legacy_same_commit (144), estimator_floor_failed (20), non_result_verdict (13) |
| `democratic_socialist` | 266 | 12 | 188 | 0 | 269 | registration_legacy_same_commit (242), estimator_floor_failed (31), non_result_verdict (13) |
| `new_keynesian` | 90 | 2 | 198 | 110 | 267 | registration_legacy_same_commit (83), estimator_floor_failed (6), non_result_verdict (5) |
| `degrowth` | 150 | 1 | 199 | 50 | 268 | registration_legacy_same_commit (149), estimator_floor_failed (20), non_result_verdict (8) |
| `social_democratic` | 277 | 13 | 187 | 0 | 280 | registration_legacy_same_commit (249), estimator_floor_failed (33), external_integrity_quarantine (9) |
| `mmt` | 206 | 15 | 185 | 0 | 265 | registration_legacy_same_commit (183), estimator_floor_failed (22), integrity_detector_flagged (10) |
| `market_socialist` | 255 | 15 | 185 | 0 | 267 | registration_legacy_same_commit (232), estimator_floor_failed (28), non_result_verdict (13) |
| `marxian` | 219 | 15 | 185 | 0 | 269 | registration_legacy_same_commit (196), estimator_floor_failed (25), non_result_verdict (11) |
| `developmentalism` | 169 | 12 | 188 | 31 | 280 | registration_legacy_same_commit (149), estimator_floor_failed (14), external_integrity_quarantine (4) |
| `institutionalism` | 159 | 14 | 186 | 41 | 260 | registration_legacy_same_commit (123), estimator_floor_failed (20), neutral_result (11) |
| `chicago_monetarism` | 233 | 24 | 176 | 0 | 265 | registration_legacy_same_commit (192), estimator_floor_failed (26), non_result_verdict (8) |
| `austrian` | 243 | 34 | 166 | 0 | 233 | registration_legacy_same_commit (175), neutral_result (25), estimator_floor_failed (23) |
| `ordoliberal` | 258 | 36 | 164 | 0 | 243 | registration_legacy_same_commit (171), neutral_result (36), estimator_floor_failed (26) |
| `classical_liberal` | 308 | 47 | 153 | 0 | 270 | registration_legacy_same_commit (211), neutral_result (36), estimator_floor_failed (30) |

## First Existing Candidates by School

This is a triage order, not permission to reclassify results. A verified preregistration with another blocker appears first; older same-commit studies require new frozen specifications and genuinely new data or holdouts.

### `eco_socialist`

- `carbon_tax_revenue_neutral_double_dividend` (regulatory.environmental_stringency): estimator_floor_failed.
- `market_order_tax_burden_gdp_pc_growth_panel` (fiscal.tax_progressivity): neutral_result.
- `market_order_tax_burden_investment_share_panel` (fiscal.tax_progressivity): neutral_result.
- `pcw100_us_mw_bite_ratio_p10_wage` (unclassified): school_score_eligible_false.
- `unemployment_benefit_duration_long_term_unemployment` (fiscal.transfer_expansion): estimator_floor_failed.
- `unemployment_benefit_generosity_employment_drag` (fiscal.transfer_expansion): external_integrity_quarantine.
- `workfare_conditionality_employment_effect` (regulatory.trade_openness): external_integrity_quarantine.
- `argentina_peronism_recurring_fiscal_inflation_cycle_1945_2023` (monetary.monetary_expansion_direction): registration_legacy_same_commit.

### `post_keynesian`

- `active_labour_market_policy_conditionality_works` (regulatory.labour_market_flexibility): estimator_floor_failed.
- `apprenticeship_employer_chamber_quality` (regulatory.labour_market_flexibility): estimator_floor_failed.
- `australia_hawke_keating_reform_long_run` (regulatory.trade_openness): external_integrity_quarantine.
- `canada_market_liberalisation_vs_state_industry_1988_2024` (regulatory.trade_openness): estimator_floor_failed.
- `firm_entry_rate_long_run_productivity` (regulatory.product_market_competition): external_integrity_quarantine.
- `frontier_income_volatility_state_allocation` (regulatory.trade_openness): external_integrity_quarantine.
- `government_consumption_share_tfp` (regulatory.trade_openness): external_integrity_quarantine.
- `market_order_tax_burden_gdp_pc_growth_panel` (fiscal.tax_progressivity): neutral_result.

### `marxist_leninist`

- `australia_hawke_keating_reform_long_run` (regulatory.trade_openness): external_integrity_quarantine.
- `canada_market_liberalisation_vs_state_industry_1988_2024` (regulatory.trade_openness): estimator_floor_failed.
- `firm_entry_rate_long_run_productivity` (regulatory.product_market_competition): external_integrity_quarantine.
- `frontier_income_volatility_state_allocation` (regulatory.trade_openness): external_integrity_quarantine.
- `government_consumption_share_tfp` (regulatory.trade_openness): external_integrity_quarantine.
- `market_order_tax_burden_gdp_pc_growth_panel` (fiscal.tax_progressivity): neutral_result.
- `market_order_tax_burden_investment_share_panel` (fiscal.tax_progressivity): neutral_result.
- `uk_thatcher_market_reform_40yr_services_frontier` (regulatory.trade_openness): estimator_floor_failed.

### `democratic_socialist`

- `australia_hawke_keating_reform_long_run` (regulatory.trade_openness): external_integrity_quarantine.
- `canada_market_liberalisation_vs_state_industry_1988_2024` (regulatory.trade_openness): estimator_floor_failed.
- `firm_entry_rate_long_run_productivity` (regulatory.product_market_competition): external_integrity_quarantine.
- `frontier_income_volatility_state_allocation` (regulatory.trade_openness): external_integrity_quarantine.
- `government_consumption_share_tfp` (regulatory.trade_openness): external_integrity_quarantine.
- `market_order_tax_burden_gdp_pc_growth_panel` (fiscal.tax_progressivity): neutral_result.
- `market_order_tax_burden_investment_share_panel` (fiscal.tax_progressivity): neutral_result.
- `pcw100_us_mw_bite_ratio_p10_wage` (unclassified): school_score_eligible_false.

### `new_keynesian`

- `contract_enforcement_fdi_productivity_spillovers` (institutional.rule_of_law): external_integrity_quarantine.
- `corruption_state_allocation_growth_interaction` (institutional.rule_of_law): external_integrity_quarantine.
- `industrial_policy_high_governance_success` (regulatory.trade_openness): external_integrity_quarantine.
- `judicial_independence_growth_persistence` (institutional.judicial_independence): estimator_floor_failed.
- `labour_flexibility_security_complement` (regulatory.labour_market_flexibility): estimator_floor_failed.
- `agricultural_productivity_poverty_reduction_panel` (unclassified): registration_legacy_same_commit.
- `agriculture_employment_transition_productivity_panel` (unclassified): registration_legacy_same_commit.
- `baa_aaa_spread_real_activity_us_1919_2026` (regulatory.labour_market_flexibility): registration_legacy_same_commit.

### `degrowth`

- `absolute_decoupling_global_material_throughput` (regulatory.trade_openness): registration_legacy_same_commit.
- `argentina_peronism_recurring_fiscal_inflation_cycle_1945_2023` (monetary.monetary_expansion_direction): registration_legacy_same_commit.
- `asian_convergence_vs_western_stagnation_2000_2023` (regulatory.product_market_competition): registration_legacy_same_commit.
- `bis_credit_gap_house_price_unemployment_lag_panel` (unclassified): registration_legacy_same_commit.
- `bis_house_price_growth_consumption_squeeze_panel` (unclassified): registration_legacy_same_commit.
- `bis_household_dsr_policy_rate_consumption_slowdown_panel` (unclassified): registration_legacy_same_commit.
- `bis_low_policy_rate_credit_gap_asset_cycle_panel` (unclassified): registration_legacy_same_commit.
- `bis_reer_appreciation_export_variety_panel` (unclassified): registration_legacy_same_commit.

### `social_democratic`

- `australia_hawke_keating_reform_long_run` (regulatory.trade_openness): external_integrity_quarantine.
- `canada_market_liberalisation_vs_state_industry_1988_2024` (regulatory.trade_openness): estimator_floor_failed.
- `contract_enforcement_fdi_productivity_spillovers` (institutional.rule_of_law): external_integrity_quarantine.
- `corruption_state_allocation_growth_interaction` (institutional.rule_of_law): external_integrity_quarantine.
- `firm_entry_rate_long_run_productivity` (regulatory.product_market_competition): external_integrity_quarantine.
- `frontier_income_volatility_state_allocation` (regulatory.trade_openness): external_integrity_quarantine.
- `government_consumption_share_tfp` (regulatory.trade_openness): external_integrity_quarantine.
- `industrial_policy_high_governance_success` (regulatory.trade_openness): external_integrity_quarantine.

### `mmt`

- `market_order_sound_money_investment_share_panel` (monetary.monetary_expansion_direction): neutral_result.
- `market_order_sound_money_private_credit_depth_panel` (monetary.monetary_expansion_direction): neutral_result.
- `market_order_tax_burden_gdp_pc_growth_panel` (fiscal.tax_progressivity): neutral_result.
- `market_order_tax_burden_investment_share_panel` (fiscal.tax_progressivity): neutral_result.
- `pcw100_us_mw_bite_ratio_p10_wage` (unclassified): school_score_eligible_false.
- `unemployment_benefit_duration_long_term_unemployment` (fiscal.transfer_expansion): estimator_floor_failed.
- `unemployment_benefit_generosity_employment_drag` (fiscal.transfer_expansion): external_integrity_quarantine.
- `workfare_conditionality_employment_effect` (regulatory.trade_openness): external_integrity_quarantine.

### `market_socialist`

- `market_order_sound_money_investment_share_panel` (monetary.monetary_expansion_direction): neutral_result.
- `market_order_sound_money_private_credit_depth_panel` (monetary.monetary_expansion_direction): neutral_result.
- `market_order_tax_burden_gdp_pc_growth_panel` (fiscal.tax_progressivity): neutral_result.
- `market_order_tax_burden_investment_share_panel` (fiscal.tax_progressivity): neutral_result.
- `pcw100_us_mw_bite_ratio_p10_wage` (unclassified): school_score_eligible_false.
- `unemployment_benefit_duration_long_term_unemployment` (fiscal.transfer_expansion): estimator_floor_failed.
- `unemployment_benefit_generosity_employment_drag` (fiscal.transfer_expansion): external_integrity_quarantine.
- `workfare_conditionality_employment_effect` (regulatory.trade_openness): external_integrity_quarantine.

### `marxian`

- `market_order_sound_money_investment_share_panel` (monetary.monetary_expansion_direction): neutral_result.
- `market_order_sound_money_private_credit_depth_panel` (monetary.monetary_expansion_direction): neutral_result.
- `market_order_tax_burden_gdp_pc_growth_panel` (fiscal.tax_progressivity): neutral_result.
- `market_order_tax_burden_investment_share_panel` (fiscal.tax_progressivity): neutral_result.
- `pcw100_us_mw_bite_ratio_p10_wage` (unclassified): school_score_eligible_false.
- `unemployment_benefit_duration_long_term_unemployment` (fiscal.transfer_expansion): estimator_floor_failed.
- `unemployment_benefit_generosity_employment_drag` (fiscal.transfer_expansion): external_integrity_quarantine.
- `workfare_conditionality_employment_effect` (regulatory.trade_openness): external_integrity_quarantine.

### `developmentalism`

- `africa_ssa_post_covid_recovery_divergence_2020_2024` (monetary.monetary_expansion_direction): external_integrity_quarantine.
- `contract_enforcement_fdi_productivity_spillovers` (institutional.rule_of_law): external_integrity_quarantine.
- `corruption_state_allocation_growth_interaction` (institutional.rule_of_law): external_integrity_quarantine.
- `industrial_policy_high_governance_success` (regulatory.trade_openness): external_integrity_quarantine.
- `judicial_independence_growth_persistence` (institutional.judicial_independence): estimator_floor_failed.
- `korea_post_chaebol_liberalisation_frontier_growth` (regulatory.trade_openness): estimator_floor_failed.
- `pcw100_us_mw_bite_ratio_p10_wage` (unclassified): school_score_eligible_false.
- `nova_industria_brasil_export_discipline_pattern_effect` (regulatory.trade_openness): non_result_verdict, replication_missing.

### `institutionalism`

- `bankruptcy_law_efficiency_capital_reallocation` (regulatory.trade_openness): estimator_floor_failed.
- `constitutional_fiscal_rules_growth_stability` (regulatory.trade_openness): estimator_floor_failed.
- `contract_enforcement_fdi_productivity_spillovers` (institutional.rule_of_law): external_integrity_quarantine.
- `corruption_state_allocation_growth_interaction` (institutional.rule_of_law): external_integrity_quarantine.
- `industrial_policy_high_governance_success` (regulatory.trade_openness): external_integrity_quarantine.
- `judicial_independence_growth_persistence` (institutional.judicial_independence): estimator_floor_failed.
- `labour_flexibility_security_complement` (regulatory.labour_market_flexibility): estimator_floor_failed.
- `market_order_control_corruption_gdp_pc_growth_panel` (institutional.rule_of_law): neutral_result.

### `chicago_monetarism`

- `australia_hawke_keating_reform_long_run` (regulatory.trade_openness): external_integrity_quarantine.
- `canada_market_liberalisation_vs_state_industry_1988_2024` (regulatory.trade_openness): estimator_floor_failed.
- `firm_entry_rate_long_run_productivity` (regulatory.product_market_competition): external_integrity_quarantine.
- `frontier_income_volatility_state_allocation` (regulatory.trade_openness): external_integrity_quarantine.
- `government_consumption_share_tfp` (regulatory.trade_openness): external_integrity_quarantine.
- `industrial_policy_high_governance_success` (regulatory.trade_openness): external_integrity_quarantine.
- `korea_post_chaebol_liberalisation_frontier_growth` (regulatory.trade_openness): estimator_floor_failed.
- `market_order_public_debt_gdp_pc_growth_panel` (regulatory.trade_openness): neutral_result.

### `austrian`

- `australia_hawke_keating_reform_long_run` (regulatory.trade_openness): external_integrity_quarantine.
- `canada_market_liberalisation_vs_state_industry_1988_2024` (regulatory.trade_openness): estimator_floor_failed.
- `firm_entry_rate_long_run_productivity` (regulatory.product_market_competition): external_integrity_quarantine.
- `frontier_income_volatility_state_allocation` (regulatory.trade_openness): external_integrity_quarantine.
- `government_consumption_share_tfp` (regulatory.trade_openness): external_integrity_quarantine.
- `industrial_policy_high_governance_success` (regulatory.trade_openness): external_integrity_quarantine.
- `market_order_capital_account_openness_fdi_inflows_share_panel` (regulatory.trade_openness): neutral_result.
- `market_order_capital_account_openness_high_tech_exports_panel` (regulatory.trade_openness): neutral_result.

### `ordoliberal`

- `australia_hawke_keating_reform_long_run` (regulatory.trade_openness): external_integrity_quarantine.
- `bankruptcy_law_efficiency_capital_reallocation` (regulatory.trade_openness): estimator_floor_failed.
- `canada_market_liberalisation_vs_state_industry_1988_2024` (regulatory.trade_openness): estimator_floor_failed.
- `constitutional_fiscal_rules_growth_stability` (regulatory.trade_openness): estimator_floor_failed.
- `contract_enforcement_fdi_productivity_spillovers` (institutional.rule_of_law): external_integrity_quarantine.
- `corruption_state_allocation_growth_interaction` (institutional.rule_of_law): external_integrity_quarantine.
- `firm_entry_rate_long_run_productivity` (regulatory.product_market_competition): external_integrity_quarantine.
- `frontier_income_volatility_state_allocation` (regulatory.trade_openness): external_integrity_quarantine.

### `classical_liberal`

- `australia_hawke_keating_reform_long_run` (regulatory.trade_openness): external_integrity_quarantine.
- `bankruptcy_law_efficiency_capital_reallocation` (regulatory.trade_openness): estimator_floor_failed.
- `canada_market_liberalisation_vs_state_industry_1988_2024` (regulatory.trade_openness): estimator_floor_failed.
- `constitutional_fiscal_rules_growth_stability` (regulatory.trade_openness): estimator_floor_failed.
- `firm_entry_rate_long_run_productivity` (regulatory.product_market_competition): external_integrity_quarantine.
- `frontier_income_volatility_state_allocation` (regulatory.trade_openness): external_integrity_quarantine.
- `government_consumption_share_tfp` (regulatory.trade_openness): external_integrity_quarantine.
- `industrial_policy_high_governance_success` (regulatory.trade_openness): external_integrity_quarantine.

## Research Sequence

1. Audit each school-specific forecast, mechanism and polarity against the original claim before a test is designed. Keep `mixed` forecasts neutral unless a new precommitted claim is authored.
2. Repair verified, genuinely runnable archival candidates only when the recorded data and estimator support the claim. Preserve failed and inconclusive results.
3. For legacy same-commit studies, freeze a new specification before a genuinely new source vintage or holdout test. Keep the older result archived.
4. Add new school-distinctive directional hypotheses where existing directional capacity is below target. Require an explicit falsifier, data source, scope, comparator and multiple-testing family.
5. Rebuild the evidence ledger, school audit and scoreboard, then verify strict second-order gates independently before making a school-level inference.
