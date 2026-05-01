# READY Problem Queue - 2026-04-30

Updated after the checklist parser patch and preflight-ready rerun sweep. Includes READY cards that remain inconclusive, partial, blocked, or otherwise not fully decisive.

## Summary

- READY problem queue: 266
- `partial_valid_but_not_decisive`: 80
- `runner_direction_ambiguity`: 78
- `multi_metric_pending_data`: 55
- `data_or_source_no_outcome_loaded`: 25
- `spec_stub_falsification`: 8
- `data_or_source_treatment_not_loaded`: 6
- `spec_missing_outcome_or_treatment`: 4
- `other_inconclusive`: 3
- `spec_missing_canonical_metrics`: 2
- `spec_interaction_not_constructible`: 2
- `data_or_source_variables_not_loaded`: 2
- `spec_missing_decomposition_channel`: 1

## Template x Bucket

| template | bucket | count |
| --- | --- | ---: |
| `panel_fe` | `runner_direction_ambiguity` | 35 |
| `multi_metric_checklist` | `multi_metric_pending_data` | 24 |
| `synth_did` | `partial_valid_but_not_decisive` | 22 |
| `synthetic_control` | `partial_valid_but_not_decisive` | 19 |
| `descriptive` | `runner_direction_ambiguity` | 17 |
| `descriptive` | `partial_valid_but_not_decisive` | 17 |
| `event_study` | `runner_direction_ambiguity` | 9 |
| `did_callaway_santanna` | `partial_valid_but_not_decisive` | 9 |
| `panel_fe` | `data_or_source_no_outcome_loaded` | 8 |
| `synthetic_control` | `multi_metric_pending_data` | 8 |
| `synth_did` | `runner_direction_ambiguity` | 8 |
| `did_callaway_santanna` | `data_or_source_no_outcome_loaded` | 7 |
| `event_study` | `partial_valid_but_not_decisive` | 6 |
| `event_study` | `multi_metric_pending_data` | 5 |
| `panel_fe` | `data_or_source_treatment_not_loaded` | 4 |
| `descriptive` | `spec_stub_falsification` | 4 |
| `synth_did` | `multi_metric_pending_data` | 4 |
| `descriptive` | `multi_metric_pending_data` | 4 |
| `did_callaway_santanna` | `multi_metric_pending_data` | 4 |
| `panel_fe_decomposition` | `runner_direction_ambiguity` | 3 |
| `synthetic_control` | `runner_direction_ambiguity` | 3 |
| `event_study` | `data_or_source_no_outcome_loaded` | 3 |
| `descriptive` | `data_or_source_no_outcome_loaded` | 3 |
| `multi_metric_checklist` | `spec_stub_falsification` | 3 |
| `did_callaway_santanna` | `runner_direction_ambiguity` | 3 |
| `panel_fe_decomposition` | `partial_valid_but_not_decisive` | 2 |
| `local_projections` | `partial_valid_but_not_decisive` | 2 |
| `panel_fe_decomposition` | `multi_metric_pending_data` | 2 |
| `did_callaway_santanna` | `data_or_source_treatment_not_loaded` | 2 |
| `local_projections` | `multi_metric_pending_data` | 2 |
| `multi_metric_checklist` | `spec_missing_canonical_metrics` | 2 |
| `panel_fe` | `spec_interaction_not_constructible` | 2 |
| `panel_fe` | `spec_missing_outcome_or_treatment` | 2 |
| `panel_fe` | `partial_valid_but_not_decisive` | 2 |
| `synthetic_control` | `data_or_source_no_outcome_loaded` | 2 |
| `panel_fe_decomposition` | `spec_missing_outcome_or_treatment` | 2 |
| `multi_metric_checklist` | `other_inconclusive` | 2 |
| `panel_fe_decomposition` | `spec_missing_decomposition_channel` | 1 |
| `local_projections` | `data_or_source_variables_not_loaded` | 1 |
| `event_study` | `spec_stub_falsification` | 1 |
| `panel_fe` | `data_or_source_variables_not_loaded` | 1 |
| `cointegration_vecm` | `multi_metric_pending_data` | 1 |
| `cointegration_vecm` | `partial_valid_but_not_decisive` | 1 |
| `lp_iv` | `multi_metric_pending_data` | 1 |
| `panel_fe_decomposition` | `data_or_source_no_outcome_loaded` | 1 |
| `did_callaway_santanna` | `other_inconclusive` | 1 |
| `synth_did` | `data_or_source_no_outcome_loaded` | 1 |

## Top Missing Tokens

| token | count |
| --- | ---: |
| `owid:systemic-banking-crises` | 3 |
| `academic:hoxby_chetty_angrist_meta_voucher_rct` | 3 |
| `academic:psid_cex_consumption_microdata` | 2 |
| `world_bank_wdi:SI.POV.NAHC` | 2 |
| `eea:eu_ets_verified_emissions` | 2 |
| `manual:constructed` | 1 |
| `bls:CES0500000008` | 1 |
| `derived:carpenter_knepper_licensing_index` | 1 |
| `eea:greenhouse_gas_inventory` | 1 |
| `ons:electricity_prices` | 1 |
| `owid:annual-co2-emissions-per-country` | 1 |
| `constructed: project-level realised abatement / stated abatement based on West et al. 2023 Science replication and Verra/Gold Standard registry vs satellite forest-loss counterfactuals (Hansen GFC). Hand-coded under derived/.` | 1 |
| `world_bank_wdi:NY.GDP.PCAP.KD` | 1 |
| `world_bank_wdi:NE.GDI.TOTL.ZS` | 1 |
| `imf:GGXWDG_NGDP` | 1 |
| `world_bank_wdi:ST.INT.ARVL` | 1 |
| `constructed: AJR (2001) extractive-vs-settler binary coding by colonial power and settler-mortality threshold` | 1 |
| `fred:A453RC1Q027SBEA / fred:A446RC1Q027SBEA` | 1 |
| `owid:primary-energy-consumption` | 1 |
| `academic:china_provincial_tfp_estimates` | 1 |
| `constructed: provincial fixed_capital_formation / Δ provincial GDP` | 1 |
| `rolling 5y` | 1 |
| `wid:tax_top_rate; OWID has owid:top-income-tax as fallback` | 1 |
| `bls:cpi_services_subindex` | 1 |
| `bls:ces_state_employment` | 1 |
| `ilostat:EAR_4MTH_SEX_RT` | 1 |
| `constructed: zero events documented for federal dollar-denominated obligations 1971-08-15 to 2024-12-31; manually coded from Moody's-S&P-Fitch sovereign-default tables` | 1 |
| `academic:bloomberg_cds` | 1 |
| `fred:auction_results; manual: TreasuryDirect auction tables` | 1 |

### data_or_source_no_outcome_loaded

| hypothesis_id | template | status | verdict/reason |
| --- | --- | --- | --- |
| `chicago_permanent_income_consumption_smoothing_microdata` | `panel_fe` | `candidate` | INCONCLUSIVE_DATA_PENDING — no outcome variable loaded; missing: ['academic:psid_cex_consumption_microdata', 'academic:psid_cex_consumption_microdata'] |
| `housing_cost_driven_real_wage_divergence` | `panel_fe` | `pre_registered` | INCONCLUSIVE_DATA_PENDING — no outcome variable loaded; missing: ['manual:constructed', 'bls:CES0500000008'] |
| `tax_inequality_biden_ctc_2021_child_poverty` | `event_study` | `draft` | INCONCLUSIVE_DATA_PENDING — no outcome variable loaded; missing: ['world_bank_wdi:SI.POV.NAHC', 'world_bank_wdi:SI.POV.NAHC'] |
| `eu_green_deal_vs_ets_emissions_mechanism` | `event_study` | `draft` | INCONCLUSIVE_DATA_PENDING — no outcome variable loaded; missing: ['eea:greenhouse_gas_inventory', 'eea:eu_ets_verified_emissions'] |
| `nuclear_phaseout_grid_reliability_cost_tradeoff` | `did_callaway_santanna` | `pre_registered` | INCONCLUSIVE_DATA_PENDING — no outcome variable loaded |
| `uk_electricity_privatisation_price_decarbonisation` | `event_study` | `draft` | INCONCLUSIVE_DATA_PENDING — no outcome variable loaded; missing: ['ons:electricity_prices', 'owid:annual-co2-emissions-per-country'] |
| `voluntary_carbon_markets_real_abatement` | `descriptive` | `draft` | INCONCLUSIVE_DATA_PENDING — no outcome variable loaded; missing: ['constructed: project-level realised abatement / stated abatement based on West et al. 2023 Science replication... |
| `caribbean_climate_resilience_panel_1990_2024` | `panel_fe` | `candidate` | INCONCLUSIVE_DATA_PENDING — no outcome variable loaded; missing: ['world_bank_wdi:NY.GDP.PCAP.KD', 'world_bank_wdi:NE.GDI.TOTL.ZS', 'imf:GGXWDG_NGDP', 'world_bank_wdi:ST.INT.ARVL'] |
| `financial_sector_profit_share_rise_1970_2007` | `descriptive` | `draft` | INCONCLUSIVE_DATA_PENDING — no outcome variable loaded; missing: ['fred:A453RC1Q027SBEA / fred:A446RC1Q027SBEA'] |
| `hayek_calculation_problem_china_soe_capital_efficiency` | `panel_fe` | `candidate` | INCONCLUSIVE_DATA_PENDING — no outcome variable loaded; missing: ['academic:china_provincial_tfp_estimates', 'constructed: provincial fixed_capital_formation / Δ provincial GDP,... |
| `lula3_industrial_policy_2023_2026_reshoring_outcomes` | `did_callaway_santanna` | `candidate` | INCONCLUSIVE_DATA_PENDING — no outcome variable loaded |
| `classical_zoning_relaxation_housing_supply_response_us_metros` | `synthetic_control` | `candidate` | INCONCLUSIVE_DATA_PENDING — no outcome variable loaded |
| `classical_occupational_licensing_consumer_loss_us_state_panel` | `panel_fe` | `candidate` | INCONCLUSIVE_DATA_PENDING — no outcome variable loaded; missing: ['bls:cpi_services_subindex', 'bls:ces_state_employment'] |
| `demo_mexico_fertility_decline_wages` | `panel_fe` | `candidate` | INCONCLUSIVE_DATA_PENDING — no outcome variable loaded; missing: ['ilostat:EAR_4MTH_SEX_RT'] |
| `labour_reform_india_industrial_codes_2020` | `did_callaway_santanna` | `candidate` | INCONCLUSIVE_DATA_PENDING — no outcome variable loaded |
| `minimum_wage_employment_effect_us_states` | `did_callaway_santanna` | `pre_registered` | INCONCLUSIVE_DATA_PENDING — no outcome variable loaded |
| `monetarist_fed_2008_great_recession_avoidable_with_constant_m_growth` | `synthetic_control` | `candidate` | INCONCLUSIVE_DATA_PENDING — no outcome variable loaded |
| `usd_issuer_solvency_no_default_post_1971` | `descriptive` | `candidate` | INCONCLUSIVE_DATA_PENDING — no outcome variable loaded; missing: ["constructed: zero events documented for federal dollar-denominated obligations 1971-08-15 to 2024-12-31; manua... |
| `banking_crisis_laeven_valencia_predictors_panel` | `panel_fe` | `candidate` | INCONCLUSIVE_DATA_PENDING — no outcome variable loaded; missing: ['owid:systemic-banking-crises'] |
| `banking_crisis_schularick_taylor_credit_boom_panel_post1980` | `panel_fe` | `candidate` | INCONCLUSIVE_DATA_PENDING — no outcome variable loaded; missing: ['owid:systemic-banking-crises', 'owid:systemic-banking-crises'] |
| `chicago_school_voucher_choice_test_score_gain_meta` | `panel_fe_decomposition` | `candidate` | INCONCLUSIVE_DATA_PENDING — no outcome variable loaded; missing: ['academic:hoxby_chetty_angrist_meta_voucher_rct', 'academic:hoxby_chetty_angrist_meta_voucher_rct', 'academic:h... |
| `liberal_free_trade_partner_growth_panel_1990_2020` | `did_callaway_santanna` | `candidate` | INCONCLUSIVE_DATA_PENDING — no outcome variable loaded |
| `welfare_reform_australia_cashless_debit_card_2015` | `synth_did` | `candidate` | INCONCLUSIVE_DATA_PENDING — no outcome variable loaded |
| `welfare_reform_prwora_single_mother_employment` | `did_callaway_santanna` | `candidate` | INCONCLUSIVE_DATA_PENDING — no outcome variable loaded |
| `welfare_transfer_india_mgnrega_pmkisan_combined` | `did_callaway_santanna` | `candidate` | INCONCLUSIVE_DATA_PENDING — no outcome variable loaded |

### multi_metric_pending_data

| hypothesis_id | template | status | verdict/reason |
| --- | --- | --- | --- |
| `china_1978_price_liberalisation_growth_decomposition` | `event_study` | `draft` | INCONCLUSIVE_DATA_PENDING — couldn't infer event_year |
| `tax_inequality_brazil_tax_base_evolution` | `panel_fe_decomposition` | `draft` | INCONCLUSIVE_DATA_PENDING — insufficient observations after listwise deletion (28) |
| `tax_inequality_chile_post_pinochet_progressivity` | `synthetic_control` | `draft` | INCONCLUSIVE_DATA_PENDING — insufficient pre-period coverage (years=0, donors=0) |
| `tax_inequality_china_vat_reform_2016` | `synthetic_control` | `draft` | INCONCLUSIVE_DATA_PENDING — insufficient pre-period coverage (years=8, donors=1) |
| `tax_inequality_estonia_1994_flat_tax_dividend_reform` | `synthetic_control` | `draft` | INCONCLUSIVE_DATA_PENDING — insufficient pre-period coverage (years=1, donors=0) |
| `tax_inequality_france_1981_wealth_tax_top_share` | `synthetic_control` | `draft` | INCONCLUSIVE_DATA_PENDING — insufficient pre-period coverage (years=6, donors=0) |
| `tax_inequality_india_gst_2017_distributional` | `synthetic_control` | `draft` | INCONCLUSIVE_DATA_PENDING — insufficient pre-period coverage (years=1, donors=0) |
| `tax_inequality_japan_consumption_tax_hikes` | `synthetic_control` | `draft` | INCONCLUSIVE_DATA_PENDING — insufficient pre-period coverage (years=0, donors=3) |
| `tax_inequality_korea_progressive_turn_2017_2020` | `synthetic_control` | `draft` | INCONCLUSIVE_DATA_PENDING — insufficient pre-period coverage (years=10, donors=1) |
| `tax_inequality_south_africa_property_tax_burden` | `synthetic_control` | `draft` | INCONCLUSIVE_DATA_PENDING — insufficient pre-period coverage (years=5, donors=0) |
| `tcja_2017_growth_effect` | `local_projections` | `draft` | INCONCLUSIVE_DATA_PENDING — insufficient obs (10); LP needs >=50 |
| `asia_taiwan_tsmc_industrial_policy_1985_2024` | `multi_metric_checklist` | `candidate` | INCONCLUSIVE_PENDING_DATA |
| `china_zero_covid_2022_2023_demand_collapse_recovery` | `multi_metric_checklist` | `candidate` | INCONCLUSIVE_PENDING_DATA |
| `japan_zero_growth_basic_wellbeing_intact` | `multi_metric_checklist` | `candidate` | INCONCLUSIVE_PENDING_DATA |
| `mena_turkey_akp_two_phase_economic_arc_2003_2024` | `synth_did` | `candidate` | INCONCLUSIVE_DATA_PENDING — insufficient pre-period coverage (years=3, donors=5) |
| `productivity_compensation_decoupling_post_1973` | `descriptive` | `draft` | INCONCLUSIVE_DATA_PENDING — insufficient pre (0) or post (41) obs |
| `ai_productivity_diffusion_2023_2026_us_sectors` | `panel_fe_decomposition` | `candidate` | INCONCLUSIVE_DATA_PENDING — insufficient observations after listwise deletion (11) |
| `corbyn_manifesto_capital_flight_prediction` | `event_study` | `draft` | INCONCLUSIVE_DATA_PENDING — insufficient pre/post obs (pre=2, post=4) |
| `demo_germany_gastarbeiter_long_run` | `descriptive` | `candidate` | INCONCLUSIVE_DATA_PENDING — insufficient pre (0) or post (29) obs |
| `emilia_romagna_coop_employment_resilience` | `synth_did` | `draft` | INCONCLUSIVE_DATA_PENDING — need >= 3 countries (1 treated + 2 donors), got 1 |
| `labour_reform_nz_employment_contracts_act_1991` | `synth_did` | `candidate` | INCONCLUSIVE_DATA_PENDING — insufficient pre-period coverage (years=0, donors=0) |
| `post_covid_labour_reallocation_us_2020_2024` | `multi_metric_checklist` | `candidate` | INCONCLUSIVE_PENDING_DATA |
| `abct_fed_funds_below_taylor_rule_capital_misallocation_2002_2007` | `multi_metric_checklist` | `candidate` | INCONCLUSIVE_PENDING_DATA |
| `argentina_fx_obligation_inflation_mechanism` | `cointegration_vecm` | `draft` | INCONCLUSIVE_DATA_PENDING — insufficient observations after listwise deletion (6) |
| `austrian_v_recovery_us_1920_no_fiscal_stim_canonical` | `multi_metric_checklist` | `candidate` | INCONCLUSIVE_PENDING_DATA |
| `fed_2022_rate_cycle_inflation_response_lag` | `lp_iv` | `candidate` | INCONCLUSIVE_DATA_PENDING — insufficient obs (7); LP needs >=50 |
| `fed_qt_balance_sheet_unwind_2022_2025_market_response` | `event_study` | `candidate` | INCONCLUSIVE_DATA_PENDING — insufficient pre/post obs (pre=2, post=4) |
| `financial_fed_reverse_repo_facility_usage_2021_2024` | `descriptive` | `candidate` | INCONCLUSIVE_DATA_PENDING — insufficient pre (1) or post (4) obs |
| `financial_negative_rates_eurozone_2014_2022` | `descriptive` | `candidate` | INCONCLUSIVE_DATA_PENDING — no DEU obs near end-period |
| `mena_egypt_floatation_episodes_2016_2024` | `event_study` | `candidate` | INCONCLUSIVE_DATA_PENDING — insufficient pre/post obs (pre=2, post=9) |
| `us_2020_2021_fiscal_inflation_transient_vs_persistent` | `local_projections` | `draft` | INCONCLUSIVE_DATA_PENDING — insufficient obs (7); LP needs >=50 |
| `austrian_kirzner_entrepreneurship_business_dynamism_decline_us_1980_2020` | `multi_metric_checklist` | `candidate` | INCONCLUSIVE_PENDING_DATA |
| `banking_crisis_2008_gfc_canonical_multimetric` | `multi_metric_checklist` | `pre_registered` | INCONCLUSIVE_PENDING_DATA |
| `banking_crisis_argentina_2001_corralito_canonical` | `multi_metric_checklist` | `pre_registered` | INCONCLUSIVE_PENDING_DATA |
| `banking_crisis_asian_financial_crisis_1997_panel` | `multi_metric_checklist` | `pre_registered` | INCONCLUSIVE_PENDING_DATA |
| `banking_crisis_brazil_proer_1995_1997` | `multi_metric_checklist` | `pre_registered` | INCONCLUSIVE_PENDING_DATA |
| `banking_crisis_china_2015_2020_panel` | `multi_metric_checklist` | `pre_registered` | INCONCLUSIVE_PENDING_DATA |
| `banking_crisis_cyprus_2013_bailin` | `multi_metric_checklist` | `pre_registered` | INCONCLUSIVE_PENDING_DATA |
| `banking_crisis_greece_2010_2018_doom_loop` | `multi_metric_checklist` | `pre_registered` | INCONCLUSIVE_PENDING_DATA |
| `banking_crisis_italy_2016_2017_mps` | `multi_metric_checklist` | `pre_registered` | INCONCLUSIVE_PENDING_DATA |
| `banking_crisis_japan_1990_lost_decade` | `multi_metric_checklist` | `pre_registered` | INCONCLUSIVE_PENDING_DATA |
| `banking_crisis_latvia_2008_parex` | `multi_metric_checklist` | `pre_registered` | INCONCLUSIVE_PENDING_DATA |
| `banking_crisis_lebanon_2019_2024_collapse` | `multi_metric_checklist` | `pre_registered` | INCONCLUSIVE_PENDING_DATA |
| `banking_crisis_russia_1998_default_canonical` | `multi_metric_checklist` | `pre_registered` | INCONCLUSIVE_PENDING_DATA |
| `banking_crisis_south_africa_african_bank_2014` | `multi_metric_checklist` | `pre_registered` | INCONCLUSIVE_PENDING_DATA |
| `banking_crisis_turkey_2001_canonical` | `multi_metric_checklist` | `pre_registered` | INCONCLUSIVE_PENDING_DATA |
| `banking_crisis_us_2023_svb_signature` | `multi_metric_checklist` | `pre_registered` | INCONCLUSIVE_PENDING_DATA |
| `banking_crisis_us_sl_crisis_1986_1995` | `multi_metric_checklist` | `pre_registered` | INCONCLUSIVE_PENDING_DATA |
| `banking_crisis_vietnam_2012_2015_restructuring` | `multi_metric_checklist` | `pre_registered` | INCONCLUSIVE_PENDING_DATA |
| `price_controls_produce_shortages_and_quality_degradation` | `synth_did` | `candidate` | INCONCLUSIVE_DATA_PENDING — insufficient pre-period coverage (years=41, donors=1) |

### runner_direction_ambiguity

| hypothesis_id | template | status | verdict/reason |
| --- | --- | --- | --- |
| `clinton_welfare_reform_deep_poverty_effect` | `event_study` | `draft` | PARTIAL — shape=ITS, mean_gap=-0.08499, z=-2.9; claim direction ambiguous |
| `demo_brazil_demographic_transition_inequality` | `panel_fe_decomposition` | `candidate` | PARTIAL — coef=-1.252, p=1 (above α=0.10); direction inconclusive |
| `r_minus_g_wealth_income_ratio_post_1980` | `panel_fe` | `draft` | PARTIAL — coef=+672.6, p=0; claim direction not auto-inferred |
| `russia_china_transition_comparison` | `descriptive` | `draft` | PARTIAL — shape=bilateral, /Δ_log/=0.0471, ratio=1.05; claim direction ambiguous |
| `tax_inequality_argentina_macri_milei_simplification` | `synthetic_control` | `draft` | PARTIAL — mean_gap=-4.148, /gap//pre_sd=2.6, p_perm=0.75; claim direction ambiguous |
| `tax_inequality_canada_2016_top_rate_increase` | `event_study` | `draft` | PARTIAL — shape=ITS, mean_gap=+0.3233, z=+0.69; claim direction ambiguous |
| `tax_inequality_italy_irpef_flattening_2002_2024` | `panel_fe` | `draft` | PARTIAL — coef=+0.02467, p=0; claim direction not auto-inferred |
| `tax_inequality_norway_wealth_tax_retention` | `synthetic_control` | `draft` | PARTIAL — mean_gap=+2.245, /gap//pre_sd=3.7, p_perm=1; claim direction ambiguous |
| `africa_south_africa_load_shedding_manufacturing_2007_2024` | `synth_did` | `candidate` | PARTIAL — mean_gap=+2348, /gap//pre_sd=6.9, p_perm=0.571; claim direction ambiguous |
| `eu_ets_absolute_decoupling_emissions_gdp` | `descriptive` | `candidate` | PARTIAL — shape=panel_summary, /Δ_log/=0.0239, ratio=1.02; claim direction ambiguous |
| `green_transition_cost_trajectory_electricity_prices` | `panel_fe` | `pre_registered` | PARTIAL — coef=-0.3408, p=0.339 (above α=0.10); direction inconclusive |
| `major_fossil_firm_reserve_vs_carbon_budget` | `descriptive` | `draft` | PARTIAL — shape=panel_summary, /Δ_log/=0; claim direction ambiguous |
| `public_transport_investment_emissions_per_capita` | `panel_fe` | `draft` | PARTIAL — coef=+5789, p=0.836 (above α=0.10); direction inconclusive |
| `africa_ghana_imf_program_2022_debt_distress` | `synth_did` | `candidate` | PARTIAL — mean_gap=+0.3876, /gap//pre_sd=1.4, p_perm=0.2; claim direction ambiguous |
| `africa_botswana_diamond_dependency_post_2014` | `synth_did` | `candidate` | PARTIAL — mean_gap=+2938, /gap//pre_sd=6.9, p_perm=0.6; claim direction ambiguous |
| `africa_ssa_post_covid_recovery_divergence_2020_2024` | `panel_fe` | `candidate` | PARTIAL — coef=-1.167, p=0.525 (above α=0.10); direction inconclusive |
| `asia_korea_chaebol_reform_2017_2024` | `descriptive` | `candidate` | PARTIAL — shape=pre_post, /Δ_log/=0.0636; threshold 5.0%, observed 6.4%; claim direction ambiguous |
| `asia_pakistan_imf_programme_cycle_1988_2024` | `panel_fe` | `candidate` | PARTIAL — coef=-1.175, p=0; claim direction not auto-inferred |
| `asia_sri_lanka_default_2022_imf_2023` | `descriptive` | `candidate` | PARTIAL — shape=pre_post, /Δ_log/=0.993; threshold 7.0%, observed 99.3%; claim direction ambiguous |
| `austrian_savings_rate_investment_quality_link` | `panel_fe` | `candidate` | PARTIAL — coef=-0.0006375, p=0.477 (above α=0.10); direction inconclusive |
| `bolivia_arce_stabilisation_2020_2024` | `descriptive` | `candidate` | PARTIAL — shape=pre_post, /Δ_log/=4.67; threshold 30.0%, observed 467.3%; claim direction ambiguous |
| `china_extra_demographic_cliff_2020_2024` | `descriptive` | `candidate` | PARTIAL — shape=pre_post, /Δ_log/=0.279; threshold 4.0%, observed 27.9%; claim direction ambiguous |
| `china_extra_made_in_china_2025_outcomes` | `panel_fe` | `candidate` | PARTIAL — coef=-2.234, p=0.258 (above α=0.10); direction inconclusive |
| `china_extra_zero_covid_exit_recovery_2023` | `descriptive` | `candidate` | PARTIAL — shape=pre_post, /Δ_log/=0.223; threshold 5.5%, observed 22.3%; claim direction ambiguous |
| `costa_rica_high_wellbeing_low_throughput_path` | `descriptive` | `candidate` | PARTIAL — shape=bilateral, /Δ_log/=0.0263, ratio=1.03; claim direction ambiguous |
| `cuba_special_period_resilience` | `descriptive` | `draft` | PARTIAL — shape=panel_summary, /Δ_log/=0.0801, ratio=1.08; claim direction ambiguous |
| `demo_higher_ed_expansion_growth` | `panel_fe` | `candidate` | PARTIAL — coef=-0.3202, p=0.461 (above α=0.10); direction inconclusive |
| `demo_israel_soviet_absorption_1989_1994` | `event_study` | `candidate` | PARTIAL — shape=ITS, mean_gap=-0.1812, z=-15; claim direction ambiguous |
| `demo_italy_spain_demographic_stagnation` | `panel_fe_decomposition` | `candidate` | PARTIAL — coef=-1.24, p=0.242 (above α=0.10); direction inconclusive |
| `demo_remittance_corridor_dependency` | `panel_fe` | `candidate` | PARTIAL — coef=+0.07958, p=0.38 (above α=0.10); direction inconclusive |
| `demo_ssa_demographic_dividend_window` | `panel_fe` | `candidate` | PARTIAL — coef=+0.3356, p=0.181 (above α=0.10); direction inconclusive |
| `demo_working_age_share_per_capita_growth` | `panel_fe` | `candidate` | PARTIAL — coef=-0.007611, p=0.92 (above α=0.10); direction inconclusive |
| `ecuador_correa_default_2008` | `event_study` | `candidate` | PARTIAL — shape=TWFE, coef=-0.003866, p=0.968; claim direction ambiguous |
| `ecuador_dollarisation_2000_stabilisation` | `synth_did` | `candidate` | PARTIAL — mean_gap=+3.052, /gap//pre_sd=0.26, p_perm=0.167; claim direction ambiguous |
| `freiburg_schuldenbremse_growth_neutral_germany_2009_2024` | `descriptive` | `candidate` | PARTIAL — shape=pre_post, /Δ_log/=0.0527; claim direction ambiguous |
| `gdp_wellbeing_divergence_income_threshold` | `panel_fe` | `draft` | PARTIAL — coef=+0.1431, p=0.79 (above α=0.10); direction inconclusive |
| `gradualist_vs_shock_therapy_transition_outcomes` | `panel_fe` | `draft` | PARTIAL — coef=-0.1868, p=0; claim direction not auto-inferred |
| `guatemala_remittance_dependence_2000_2024` | `panel_fe` | `candidate` | PARTIAL — coef=+1.741, p=nan (above α=0.10); direction inconclusive |
| `jamaica_imf_debt_restructuring_2010_2024` | `descriptive` | `candidate` | PARTIAL — shape=panel_summary, /Δ_log/=0.0648, ratio=0.937; threshold 140.0%, observed 6.5%; claim direction ambiguous |
| `latam_extra_commodity_cycle_dependence_1990_2024` | `panel_fe` | `candidate` | PARTIAL — coef=+0.01623, p=0.304 (above α=0.10); direction inconclusive |
| `latam_extra_fiscal_rule_adoption_panel_1999_2024` | `did_callaway_santanna` | `candidate` | PARTIAL — ATT=-22.28, p=8.45e-178, N=432, treated_countries=5; claim direction ambiguous |
| `latam_extra_inflation_targeting_diff_in_diff_1999_2024` | `did_callaway_santanna` | `candidate` | PARTIAL — ATT=-56.15, p=3.31e-286, N=458, treated_countries=10; claim direction ambiguous |
| `mena_gcc_oil_price_decoupling_2014_2024` | `panel_fe` | `candidate` | PARTIAL — coef=+2.825, p=0.108 (above α=0.10); direction inconclusive |
| `mittelstand_institutional_productivity_effect` | `panel_fe` | `draft` | PARTIAL — coef=-0.005077, p=0.968 (above α=0.10); direction inconclusive |
| `paraguay_long_stable_growth_2003_2024` | `panel_fe` | `candidate` | PARTIAL — coef=-0.4028, p=0; claim direction not auto-inferred |
| `peru_fujimori_shock_therapy_1990_2000` | `synth_did` | `candidate` | PARTIAL — mean_gap=-0.7927, /gap//pre_sd=7.8, p_perm=0.4; claim direction ambiguous |
| `pinochet_chile_rapid_liberalisation_growth_collapse` | `synth_did` | `draft` | PARTIAL — mean_gap=+0.3637, /gap//pre_sd=6.2, p_perm=1; claim direction ambiguous |
| `post_soviet_transition_institutional_variation` | `panel_fe` | `pre_registered` | PARTIAL — coef=-9.325e-10, p=0.309 (above α=0.10); direction inconclusive |
| `sea_malaysia_1mdb_economic_effect_2015_2024` | `panel_fe` | `candidate` | PARTIAL — coef=-0.0341, p=0.937 (above α=0.10); direction inconclusive |
| `trinidad_tobago_oil_dependence_2008_2024` | `panel_fe` | `candidate` | PARTIAL — coef=-0.2814, p=nan (above α=0.10); direction inconclusive |

### partial_valid_but_not_decisive

| hypothesis_id | template | status | verdict/reason |
| --- | --- | --- | --- |
| `lula_bolsa_familia_poverty_reduction_decomposition_2003_2010` | `panel_fe_decomposition` | `pre_registered` | partial — Some Shapley conditions met but not all: BF+MW poverty share 9% < 40%; BF+MW Gini share 6% < 30%. Brazil 2003→2010 delta: poverty -9.4pp, Gini -4.3. |
| `tax_inequality_australia_2009_top_rate_response` | `local_projections` | `draft` | PARTIAL — cumulative_effect=+0.09768, h=5, p_h=0.776 (above α=0.10) |
| `tax_inequality_bush_2003_dividend_capgains_cut` | `event_study` | `draft` | PARTIAL — shape=ITS, opposite sign but small (mean_gap=-0.6187, z=-1) |
| `tax_inequality_clinton_1993_obra_top_bracket` | `event_study` | `draft` | PARTIAL — shape=ITS, opposite sign but small (mean_gap=-1.031, z=-1.2) |
| `tax_inequality_france_2017_isf_to_ifi_abolition` | `synthetic_control` | `draft` | PARTIAL — mean_gap=+1.331, /gap//pre_sd=2.2, p_perm=1 (gap below 0.5×pre_sd or placebo p≥0.10) |
| `tax_inequality_germany_2000_schroder_reform` | `synthetic_control` | `draft` | PARTIAL — mean_gap=+0.3903, /gap//pre_sd=0.43, p_perm=0.4 (gap below 0.5×pre_sd or placebo p≥0.10) |
| `tax_inequality_greece_troika_tax_hikes_2010_2018` | `synthetic_control` | `draft` | PARTIAL — mean_gap=+3.175, /gap//pre_sd=3.7, p_perm=0.333 (gap below 0.5×pre_sd or placebo p≥0.10) |
| `tax_inequality_mexico_2014_reform_distributional` | `synthetic_control` | `draft` | PARTIAL — mean_gap=+14.74, /gap//pre_sd=1.8, p_perm=1 (gap below 0.5×pre_sd or placebo p≥0.10) |
| `tax_inequality_nz_2010_gst_rate_swap` | `synthetic_control` | `draft` | PARTIAL — mean_gap=+4.113, /gap//pre_sd=1.1, p_perm=0.333 (gap below 0.5×pre_sd or placebo p≥0.10) |
| `tax_inequality_reagan_1981_top_share_response` | `did_callaway_santanna` | `draft` | PARTIAL — ATT=-8.931, p=0.858, N=51, treated_countries=4 (above α=0.10) |
| `tax_inequality_spain_top_rate_dynamics` | `local_projections` | `draft` | PARTIAL — cumulative_effect=-0.1918, h=5, p_h=0.556 (above α=0.10) |
| `tax_inequality_sweden_1991_dual_income_reform` | `did_callaway_santanna` | `draft` | PARTIAL — ATT=+0.06163, p=0.894, N=51, treated_countries=1 (above α=0.10) |
| `tax_inequality_tcja_2017_decile_incidence` | `descriptive` | `draft` | PARTIAL — shape=pre_post, sign matches but magnitude below threshold; /Δ_log/=0.07; threshold 35.0%, observed 7.0% |
| `tax_inequality_thatcher_1988_top_rate_cut` | `synthetic_control` | `draft` | PARTIAL — mean_gap=+0.06276, /gap//pre_sd=0.21, p_perm=1 (gap below 0.5×pre_sd or placebo p≥0.10) |
| `tax_inequality_uk_50pct_rate_2010_2013` | `event_study` | `draft` | PARTIAL — shape=ITS, sign matches claim - but magnitude small (mean_gap=-4.02, z=-7.3) |
| `eu_post_2021_gas_shock_industrial_output_impact` | `did_callaway_santanna` | `pre_registered` | PARTIAL — ATT=+6.187e+09, p=0.755, N=91, treated_countries=14 (above α=0.10) |
| `nordstream_sabotage_2022_european_energy_security_pivot` | `descriptive` | `candidate` | PARTIAL — shape=panel_summary, sign matches but magnitude below threshold; /Δ_log/=0; threshold 40.0%, observed 0.0% |
| `africa_nigeria_fuel_subsidy_removal_2023` | `synth_did` | `candidate` | PARTIAL — mean_gap=+0.3137, /gap//pre_sd=1.3, p_perm=1 (gap below 0.5×pre_sd or placebo p≥0.10) |
| `mena_egypt_sisi_macro_stabilisation_2014_2024` | `synth_did` | `candidate` | PARTIAL — mean_gap=-67.56, /gap//pre_sd=0.94, p_perm=0.75 (gap below 0.5×pre_sd or placebo p≥0.10) |
| `uk_truss_mini_budget_currency_sovereign_mechanism` | `event_study` | `draft` | partial — Both mechanism legs are directionally consistent but at least one fails the SUPPORTED threshold: FX leg holds (5.02% trough decline); yield leg partial (61bp spike, 28... |
| `africa_ethiopia_gerd_economic_effect_2011_2024` | `synth_did` | `candidate` | PARTIAL — mean_gap=-132.4, /gap//pre_sd=2.7, p_perm=0.714 (gap below 0.5×pre_sd or placebo p≥0.10) |
| `africa_ethiopia_tigray_war_economic_collapse_2020_2022` | `synth_did` | `candidate` | PARTIAL — mean_gap=+8.996e+10, /gap//pre_sd=5.5, p_perm=0.167 (gap below 0.5×pre_sd or placebo p≥0.10) |
| `africa_kenya_mpesa_digital_payments_formalisation_2007_2024` | `synth_did` | `candidate` | PARTIAL — mean_gap=+399.5, /gap//pre_sd=12, p_perm=0.75 (gap below 0.5×pre_sd or placebo p≥0.10) |
| `africa_rwanda_post_genocide_growth_model_1995_2024` | `synth_did` | `candidate` | PARTIAL — mean_gap=+330.7, /gap//pre_sd=4.4, p_perm=0.571 (gap below 0.5×pre_sd or placebo p≥0.10) |
| `bolivia_morales_resource_nationalism_2006_2019` | `synth_did` | `candidate` | PARTIAL — mean_gap=-1.048, /gap//pre_sd=25, p_perm=0.25 (gap below 0.5×pre_sd or placebo p≥0.10) |
| `demo_china_one_child_long_run_growth` | `synthetic_control` | `candidate` | PARTIAL — mean_gap=+7.502, /gap//pre_sd=8, p_perm=0.2 (gap below 0.5×pre_sd or placebo p≥0.10) |
| `demo_japan_refusal_immigration_counterfactual` | `descriptive` | `candidate` | PARTIAL — shape=panel_summary, sign opposite claim + but magnitude tiny; /Δ_log/=0.0834, ratio=0.92 |
| `ethiopia_developmental_state_growth_effect` | `synth_did` | `draft` | partial — Ethiopia grew faster than the peer median (+20.6 log-points) and ranked #3/12, but did not meet both primary thresholds (rank #1 AND gap >= 20 log-points). Synthetic c... |
| `eu_green_deal_decoupling_pace_vs_target` | `descriptive` | `draft` | SUPPORTED — EU panel shows partial decoupling 2019->2023: mean per-capita CO2 -18.3%, mean per-capita real GDP +4.6%. 13/16 countries showed both falling emissions and rising GD... |
| `guyana_suriname_oil_discovery_2015_2024` | `descriptive` | `candidate` | PARTIAL — shape=panel_summary, sign matches but magnitude below threshold; /Δ_log/=0.0706, ratio=1.07; threshold 170.0%, observed 7.1% |
| `haiti_governance_collapse_economic_effect_2010_2024` | `descriptive` | `candidate` | PARTIAL — shape=pre_post, sign matches but magnitude below threshold; /Δ_log/=0.0225; threshold 5.0%, observed 2.2% |
| `high_income_material_footprint_unchanged_post_2000` | `descriptive` | `candidate` | PARTIAL — shape=panel_summary, sign opposite claim - but magnitude tiny; /Δ_log/=0.0285, ratio=1.03; threshold 10.0%, observed 2.9% |
| `india_extra_demonetisation_2016_economic_effect` | `descriptive` | `candidate` | PARTIAL — shape=pre_post, sign matches but magnitude below threshold; /Δ_log/=0.0932; threshold 86.0%, observed 9.3% |
| `mena_iran_sanctions_economic_effect_2018_2024` | `synth_did` | `candidate` | PARTIAL — mean_gap=+772.4, /gap//pre_sd=4.3, p_perm=0.857 (gap below 0.5×pre_sd or placebo p≥0.10) |
| `mena_saudi_vision_2030_diversification_2016_2024` | `synth_did` | `candidate` | PARTIAL — mean_gap=+5.962e+11, /gap//pre_sd=8, p_perm=0.167 (gap below 0.5×pre_sd or placebo p≥0.10) |
| `reagan_tax_cuts_growth_effect` | `event_study` | `draft` | PARTIAL — shape=TWFE, coef=+0.006685, p=0.838 (above α=0.10) |
| `sea_vietnam_doi_moi_followon_growth_1995_2024` | `synth_did` | `candidate` | PARTIAL — mean_gap=+0.465, /gap//pre_sd=4.8, p_perm=0.143 (gap below 0.5×pre_sd or placebo p≥0.10) |
| `soviet_industrial_catch_up_1928_1940` | `descriptive` | `draft` | partial — USSR cum-log growth +0.594 exceeds WE-mean +0.188 (differential +0.406) but falls short of the +0.50 log threshold the spec requires. Direction of the claim holds; mag... |
| `uk_cameron_osborne_austerity_output_effect` | `synth_did` | `draft` | partial — debt-target check passes (87.3% vs target 67.0%, overshoot +20.3pp) but UK output gap to donor mean = -0.0083 log-pts > -0.02 — output did not fall below counterfactua... |
| `us_1945_1973_labour_compact_productivity_wage_link` | `descriptive` | `draft` | PARTIAL — shape=pre_post, sign matches; /Δ_log/=0.361; threshold not extracted |
| `us_eu_divergence_decomposition` | `panel_fe` | `pre_registered` | partial — gap widened +0.044 log-points but less than 0.10 threshold |
| `cuba_health_outcomes_vs_non_latam_market_peers` | `descriptive` | `candidate` | PARTIAL — Cuba clears two of the three harder gates in the 21-country non-LATAM market-economy pool. Ranks: LE #6/21, IMR #7/21, income #18/21; mean-health-vs-income gap 11.5. M... |
| `vienna_social_housing_rent_burden_comparative` | `descriptive` | `draft` | partial — Only the rent-burden primary held; the HPI-no-runaway primary failed. AT overburden gap -2.8pp; AT cum HPI log-change +74.6% vs pool +43.5% (+31.1pp). |
| `fiscal_rule_presence_dampens_statist_drift` | `descriptive` | `pre_registered` | PARTIAL — gap is in the predicted direction (rule-bound -4.07 vs rule-free -1.10, gap -2.97) but Mann-Whitney one-sided p = 0.2685 fails to reject 0.10. |
| `initial_state_share_predicts_drift_reversal` | `descriptive` | `pre_registered` | partial — Direction is correct (β = -0.0245) but neither the significance threshold (p = 0.8254) nor the explanatory threshold (R² = 0.002) is met. Suggestive only. |
| `nordic_outcome_persistence_decomposition_v2` | `panel_fe_decomposition` | `pre_registered` | partially supported (primary outcome improved materially but did not meet 0.30 threshold) |
| `rule_of_law_institutional_growth` | `panel_fe` | `pre_registered` | PARTIAL — only 0 of 3 legs pass falsification; panel β_RL=-0.0114 (p=0.713); cross-section β_RL=+0.0046 (p=0.066) |
| `friedman_negative_income_tax_labour_supply_smaller_than_predicted` | `did_callaway_santanna` | `candidate` | PARTIAL — ATT=+20.8, p=nan, N=53, treated_countries=1 (above α=0.10) |
| `labour_reform_australia_workchoices_1996_employment` | `synth_did` | `candidate` | PARTIAL — mean_gap=+0.3444, /gap//pre_sd=0.35, p_perm=0.875 (gap below 0.5×pre_sd or placebo p≥0.10) |
| `labour_reform_colombia_2002_uribe_employment` | `synth_did` | `candidate` | PARTIAL — mean_gap=+2.534, /gap//pre_sd=0.58, p_perm=0.714 (gap below 0.5×pre_sd or placebo p≥0.10) |

### data_or_source_treatment_not_loaded

| hypothesis_id | template | status | verdict/reason |
| --- | --- | --- | --- |
| `occupational_licensing_productivity_drag` | `panel_fe` | `draft` | INCONCLUSIVE_DATA_PENDING — treatment 'occupational_licensing_scope_index' not loaded; missing: ['derived:carpenter_knepper_licensing_index'] |
| `free_community_college_enrolment_completion` | `did_callaway_santanna` | `draft` | INCONCLUSIVE_DATA_PENDING — treatment 'tennessee_promise_2015' not loaded |
| `colonial_institutions_post_independence_growth` | `panel_fe` | `draft` | INCONCLUSIVE_DATA_PENDING — treatment 'settler_inclusive_institutions_indicator' not loaded; missing: ['constructed: AJR (2001) extractive-vs-settler binary coding by colonial p... |
| `gdp_energy_coupling_1945_1973` | `panel_fe` | `draft` | INCONCLUSIVE_DATA_PENDING — treatment 'log_primary_energy_consumption' not loaded; missing: ['owid:primary-energy-consumption'] |
| `top_marginal_rate_growth_tradeoff` | `panel_fe` | `draft` | INCONCLUSIVE_DATA_PENDING — treatment 'top_marginal_income_tax_rate' not loaded; missing: ['wid:tax_top_rate; OWID has owid:top-income-tax as fallback'] |
| `trump_tariff_manufacturing_reshoring_effect` | `did_callaway_santanna` | `draft` | INCONCLUSIVE_DATA_PENDING — treatment 'trump_tariff_2018_indicator' not loaded |

### spec_missing_decomposition_channel

| hypothesis_id | template | status | verdict/reason |
| --- | --- | --- | --- |
| `uk_thatcher_era_labour_share_decline_1979_1990` | `panel_fe_decomposition` | `draft` | INCONCLUSIVE_DATA_PENDING — no decomposition channel loaded; missing: [] |

### spec_stub_falsification

| hypothesis_id | template | status | verdict/reason |
| --- | --- | --- | --- |
| `eu_ets_emissions_reduction_vs_1p5c_pathway` | `descriptive` | `draft` | INCONCLUSIVE_DATA_PENDING — falsification rule not sharpened — auto-grader refuses to grade against the generic stub boilerplate. Promote the spec (replace falsification.rule wi... |
| `argentina_institutional_instability_decline` | `multi_metric_checklist` | `draft` | INCONCLUSIVE_DATA_PENDING |
| `material_footprint_cap_feasibility` | `multi_metric_checklist` | `draft` | INCONCLUSIVE_DATA_PENDING |
| `mondragon_cooperative_resilience` | `multi_metric_checklist` | `draft` | INCONCLUSIVE_DATA_PENDING |
| `soviet_collectivisation_agricultural_marketings` | `descriptive` | `draft` | INCONCLUSIVE_DATA_PENDING — falsification rule not sharpened — auto-grader refuses to grade against the generic stub boilerplate. Promote the spec (replace falsification.rule wi... |
| `meidner_wage_earner_fund_capital_flight` | `event_study` | `draft` | INCONCLUSIVE_DATA_PENDING — falsification rule not sharpened — auto-grader refuses to grade against the generic stub boilerplate. Promote the spec (replace falsification.rule wi... |
| `friedman_schwartz_great_depression_monetary_cause` | `descriptive` | `draft` | INCONCLUSIVE_DATA_PENDING — falsification rule not sharpened — auto-grader refuses to grade against the generic stub boilerplate. Promote the spec (replace falsification.rule wi... |
| `great_depression_over_accumulation_vs_monetary_cause` | `descriptive` | `draft` | INCONCLUSIVE_DATA_PENDING — falsification rule not sharpened — auto-grader refuses to grade against the generic stub boilerplate. Promote the spec (replace falsification.rule wi... |

### spec_missing_canonical_metrics

| hypothesis_id | template | status | verdict/reason |
| --- | --- | --- | --- |
| `chile_post_1990_institutional_premium` | `multi_metric_checklist` | `draft` | INCONCLUSIVE_DATA_PENDING |
| `singapore_temasek_public_ownership_efficiency` | `multi_metric_checklist` | `draft` | INCONCLUSIVE_DATA_PENDING |

### spec_interaction_not_constructible

| hypothesis_id | template | status | verdict/reason |
| --- | --- | --- | --- |
| `india_extra_aadhaar_upi_productivity` | `panel_fe` | `candidate` | INCONCLUSIVE_DATA_PENDING — interaction term requested but no loadable constructed interaction variable is defined. The generic panel_fe runner would otherwise grade a main-effe... |
| `industrial_policy_governance_capacity_conditionality` | `panel_fe` | `draft` | INCONCLUSIVE_DATA_PENDING — interaction term requested but no loadable constructed interaction variable is defined. The generic panel_fe runner would otherwise grade a main-effe... |

### spec_missing_outcome_or_treatment

| hypothesis_id | template | status | verdict/reason |
| --- | --- | --- | --- |
| `uk_nationalised_industry_investment_rates` | `panel_fe` | `pre_registered` | INCONCLUSIVE_DATA_PENDING — no outcome or no treatment variable in spec |
| `immigration_crime_rate_vs_native_controlled` | `panel_fe_decomposition` | `pre_registered` | INCONCLUSIVE_DATA_PENDING — no outcome or no treatment variable in spec |
| `second_generation_education_outcomes_by_origin` | `panel_fe_decomposition` | `pre_registered` | INCONCLUSIVE_DATA_PENDING — no outcome or no treatment variable in spec |
| `fiat_expansion_erodes_currency_purchasing_power_long_run` | `panel_fe` | `pre_registered` | INCONCLUSIVE_DATA_PENDING — no outcome or no treatment variable in spec |

### data_or_source_variables_not_loaded

| hypothesis_id | template | status | verdict/reason |
| --- | --- | --- | --- |
| `biden_ira_chips_fiscal_inflation_pass_through` | `local_projections` | `draft` | INCONCLUSIVE_DATA_PENDING — variables not loaded: ['ira_chips_fiscal_impulse'] |
| `abct_credit_boom_predicts_capital_misallocation_oecd` | `panel_fe` | `candidate` | INCONCLUSIVE_DATA_PENDING — variables not loaded: ['bis:WS_CREDIT', 'bis:WS_CREDIT_GAP'] |

### other_inconclusive

| hypothesis_id | template | status | verdict/reason |
| --- | --- | --- | --- |
| `mena_lebanon_currency_collapse_real_economy_2019_2024` | `multi_metric_checklist` | `pre_registered` | REFUTED |
| `banking_crisis_mexico_tequila_1994_canonical` | `multi_metric_checklist` | `pre_registered` | REFUTED |
| `eu_chemical_reach_regulation_firm_exit_effect` | `did_callaway_santanna` | `pre_registered` | SUPPORTED at aggregate proxy — EU industrial VA per capita post-2007 ATT = -0.0314 log (threshold β<-0.02 met); pre-trend clean. This is stronger than YAML's prior expected; SME... |
