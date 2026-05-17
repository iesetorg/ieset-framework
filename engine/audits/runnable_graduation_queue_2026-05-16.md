# Runnable Graduation Queue - 2026-05-16

Purpose: quantify how many hypotheses can be rerun and plausibly graduate from inconclusive status with the current local corpus, including the newly acquired WITS product-concentration benchmark and the resource-developmentalism subtype work.

## Headline

Immediate rerun/graduation queue: **66 preflight-ready inconclusive runs**.

These are existing inconclusive run artifacts whose current specs now pass the local preflight check: the runner can build the panel and identify both outcome and treatment/decomposition variables. They are the best first batch to rerun.

## Corpus Counts

| Item | Count |
| --- | ---: |
| Hypothesis YAML files scanned | 1,628 |
| Existing run diagnostics | 1,607 |
| Source-ready supported-template specs | 1,210 |
| Specs still needing data | 394 |
| Specs needing/unsupported templates | 24 |
| Existing non-inconclusive runs | 1,414 |
| Existing inconclusive runs | 193 |

Normalized current run verdicts:

| Current verdict family | Count |
| --- | ---: |
| Partial | 787 |
| Supported or supported variant | 456 |
| Refuted / weakened variant | 162 |
| Inconclusive | 193 |
| Unknown | 8 |
| Blocked | 1 |

## Inconclusive Preflight State

| State | Count |
| --- | ---: |
| Preflight-ready now | 66 |
| Preflight-blocked | 79 |
| Unknown template | 37 |
| Missing spec variables | 8 |
| Stub falsification rule | 3 |

## Preflight-Ready Queue By Runner

| Runner template | Count |
| --- | ---: |
| `panel_fe` | 21 |
| `synth_did` | 18 |
| `descriptive` | 7 |
| `event_study` | 7 |
| `did_callaway_santanna` | 5 |
| `panel_fe_decomposition` | 5 |
| `local_projections` | 3 |

## Immediate 66-Candidate Queue

### Descriptive

- `demo_germany_gastarbeiter_long_run`
- `financial_fed_reverse_repo_facility_usage_2021_2024`
- `friedman_schwartz_great_depression_monetary_cause`
- `great_depression_over_accumulation_vs_monetary_cause`
- `nuclear_phaseout_accident_risk_reduction_value`
- `productivity_compensation_decoupling_post_1973`
- `welfare_pension_mexico_universal_2023_fiscal_effect`

### DiD / Callaway-Santanna

- `child_benefit_expansion_child_poverty_effect`
- `chips_act_2022_semiconductor_capacity_2024_2027`
- `welfare_transfer_china_dibao_rural_pension_2009`
- `welfare_transfer_indonesia_pkh_blt_2007_2022`
- `welfare_transfer_kenya_hsnp_2015_consumption_smoothing`

### Event Study

- `corbyn_manifesto_capital_flight_prediction`
- `fed_qt_balance_sheet_unwind_2022_2025_market_response`
- `macron_labour_tax_employment_distribution`
- `mena_egypt_floatation_episodes_2016_2024`
- `welfare_reform_uk_universal_credit_employment_effect`
- `welfare_transfer_us_arpa_expanded_ctc_2021`
- `wto_accession_productivity_spillover_panel`

### Local Projections

- `fed_2022_rate_cycle_inflation_response_lag`
- `tcja_2017_growth_effect`
- `welfare_transfer_hong_kong_cash_payout_2020`

### Panel FE

- `asia_bangladesh_apparel_growth_1985_2024`
- `asia_pakistan_imf_programme_cycle_1988_2024`
- `australia_hawke_keating_reform_long_run`
- `austrian_monetary_expansion_asset_bubble_not_cpi_panel`
- `central_bank_balance_sheet_cpi_decoupling_panel_2008_2020`
- `china_soe_vs_cee_privatised_growth`
- `competition_enforcement_consumer_welfare_effect`
- `demo_canada_points_system_immigration`
- `demo_life_expectancy_lfp_panel`
- `demo_mexico_fertility_decline_wages`
- `export_openness_agricultural_diversification`
- `gfc_balance_sheet_recession_post_2008_household_dual_mandate`
- `global_value_chain_participation_upgrade`
- `high_income_escape_market_openness_1950_2024`
- `india_extra_aadhaar_upi_productivity`
- `interest_rate_hike_distributional_upward_redistribution`
- `labour_market_reform_almp_complementarity_effect`
- `monopoly_capital_concentration_markup_link`
- `oecd_product_market_deregulation_tfp_panel`
- `universal_healthcare_cost_outcome_oecd`
- `welfare_transfer_finland_basic_income_experiment_2017`

### Panel FE Decomposition

- `demo_brazil_demographic_transition_inequality`
- `post_covid_inflation_episode_supply_vs_demand_decomposition`
- `tax_inequality_brazil_tax_base_evolution`
- `uk_real_wage_stagnation_2008_present_decomposition`
- `zimbabwe_land_reform_cause_decomposition`

### Synth-DiD / Synthetic Control

- `labour_reform_canada_1990s_ui_reform_nairu`
- `labour_reform_nz_employment_contracts_act_1991`
- `labour_reform_schroeder_agenda_2010_long_run_inequality`
- `labour_reform_sweden_1990s_employment_recovery`
- `labour_reform_uk_thatcher_union_law_1980s`
- `mena_turkey_akp_two_phase_economic_arc_2003_2024`
- `price_controls_produce_shortages_and_quality_degradation`
- `singapore_cpf_institutional_complementarity`
- `tax_inequality_chile_post_pinochet_progressivity`
- `tax_inequality_china_vat_reform_2016`
- `tax_inequality_estonia_1994_flat_tax_dividend_reform`
- `tax_inequality_france_1981_wealth_tax_top_share`
- `tax_inequality_india_gst_2017_distributional`
- `tax_inequality_japan_consumption_tax_hikes`
- `tax_inequality_korea_progressive_turn_2017_2020`
- `tax_inequality_south_africa_property_tax_burden`
- `wealth_tax_capital_flight_revenue_yield_gap`
- `welfare_reform_new_zealand_1991_benefit_cuts_effect`

## WITS / Product-Trade Update

New loadable series:

- `wits:export_product_hhi_wits`

Local vintage:

- `data/vintages/wits/export_product_hhi_wits@2026-05-16T094546Z.parquet`

Coverage:

- 4,669 exporter-year rows
- 207 reporter ISO3s
- 1988-2022
- exporter-to-world rows only (`PartnerISO3 == WLD`)

This unblocks a benchmark product-concentration outcome, but it does not yet replace BACI/Comtrade product-line microdata. Existing trade/product hypotheses that mention product concentration still need additional mapping or other missing inputs before clean graduation:

- `export_complexity_market_access_vs_subsidy`
- `consumer_choice_variety_trade_market_reform`
- `quality_adjusted_consumption_market_liberal_panel`

## Resource Developmentalism Status

The resource-developmentalism diagnosis is better positioned but should not graduate scoreboard-safe yet.

Now available:

- manual subtype coding sidecar: `data/manual/resource_developmentalism_subtype_coding_2026-05-16.csv`
- product-concentration benchmark: `wits:export_product_hhi_wits`

Still needed before graduation:

- integrate the subtype coding into movement vintages or a bespoke runner sidecar
- rerun against WITS product HHI, broad WDI HHI, TFP growth, manufacturing share, and lag/cumulative exposure
- regenerate manifest/evidence packet only after the hardened run exists

## Recommended Batch Order

1. Run the 66 preflight-ready inconclusives in a capped batch, ideally 20-25 first to observe runner failure modes.
2. Prioritize low-risk generic templates first: `descriptive`, `event_study`, `local_projections`, and `panel_fe`.
3. Run `synth_did` after the generic batch because it is more likely to need case-by-case donor/event sanity checks.
4. Keep resource-developmentalism in a bespoke prototype lane rather than the generic 66-run graduation queue.
