# Uncommitted ready hypotheses - 2026-05-16

This is a cleanup ledger for the current dirty tree. It separates modified hypothesis runs that have usable, non-inconclusive verdicts from modified runs that are still blocked.

## Counts

- Modified `engine/runs/*/diagnostics.json`: 90
- Ready non-inconclusive hypothesis runs: 41
- Still blocked / inconclusive modified runs: 49

Ready verdict mix:

- SUPPORTED: 14
- REFUTED: 4
- PARTIAL: 16
- WEAKENED: 7

## Ready to include

These runs have modified diagnostics/result cards with a non-inconclusive verdict. `WEAKENED` means the artifact is usable but caveated, usually because one registered gate is still missing.

| Verdict | Hypothesis | Template | Short reason |
| --- | --- | --- | --- |
| SUPPORTED | `abenomics_monetary_fiscal_coordination_effect` | event_study | ITS post-2013 gap is positive relative to pretrend. |
| SUPPORTED | `asia_bangladesh_apparel_growth_1985_2024` | descriptive | Manufacturing share +6.75pp and BGD-PAK GDP-pc growth gap +2.78pp/yr. |
| SUPPORTED | `asia_pakistan_imf_programme_cycle_1988_2024` | panel_fe | Coefficient -2.287, p≈1.24e-14. |
| SUPPORTED | `demo_mexico_fertility_decline_wages` | panel_fe | Coefficient +0.1242, p≈8.99e-47. |
| SUPPORTED | `fiat_expansion_erodes_currency_purchasing_power_long_run` | descriptive | 7/7 fiat currencies lost purchasing power against at least one hard-asset benchmark. |
| SUPPORTED | `financial_fed_reverse_repo_facility_usage_2021_2024` | descriptive | ON RRP peaked at USD 2,554bn and fell USD 2,314bn by 2024Q3. |
| SUPPORTED | `labour_market_reform_almp_complementarity_effect` | panel_fe | Coefficient -3.813, p≈0.008. |
| SUPPORTED | `nuclear_phaseout_accident_risk_reduction_value` | descriptive | Panel summary sign matches; ratio 9.61. |
| SUPPORTED | `trade_lib_argentina_mercosur_industrial_effect` | descriptive | ARG manufacturing-share change differed from comparators by only +1.6pp. |
| SUPPORTED | `trade_lib_colombia_us_fta_2012` | descriptive | COL openness change was within +1.4pp of comparator change. |
| SUPPORTED | `trade_lib_egypt_fta_cascade` | descriptive | Openness rose +16.1pp by 2007-2010, then post-2011 mean sat -21.3pp below peak. |
| SUPPORTED | `trade_lib_india_1991_tariff_cut_export_response` | descriptive | Trade openness rose +14.7pp, clearing the +10pp gate. |
| SUPPORTED | `trade_lib_south_africa_sadc_trade` | descriptive | ZAF openness changed +13.3pp, inside the registered [-5,+20]pp band. |
| SUPPORTED | `universal_healthcare_cost_outcome_oecd` | panel_fe | Coefficient -0.5591, p≈0.0028. |
| REFUTED | `monetary_finance_zlb_no_inflation` | descriptive | USA CPI breaches the registered >3% gates; Eurozone CPI not loaded. |
| REFUTED | `trade_lib_chile_bilateral_fta_cascade` | descriptive | CHL openness rose +7.3pp but comparator differential moved -9.0pp. |
| REFUTED | `trade_lib_indonesia_1980s_1990s_unilateral` | descriptive | Trade openness rose only +1.9pp, below the +5pp refutation gate. |
| REFUTED | `trade_lib_mexico_eu_fta_2000` | descriptive | MEX openness change lagged comparators by 6.1pp. |
| WEAKENED | `central_bank_balance_sheet_cpi_decoupling_panel_2008_2020` | descriptive | USA core-CPI and expectations gates clear; Japan/ECB/BoE gates not loaded. |
| WEAKENED | `japan_public_debt_solvency_inflation_independence` | descriptive | Crossed debt thresholds clear yield/CPI gates; local IMF vintage does not cross 250%. |
| WEAKENED | `japan_sargent_wallace_refutation_1990_2024` | descriptive | No observed yield/CPI/regression breach; 250% debt, CPI coverage, and distress-event gates caveated. |
| WEAKENED | `tcja_2017_growth_effect` | local_projections | GDP gate clears at 0.97pp; PNFI below pretrend; EMTR-elasticity gate not loaded. |
| WEAKENED | `us_dollar_issuer_solvency_record` | descriptive | Zero coded qualifying events; default/CDS/auction gates not machine-fetched. |
| WEAKENED | `usd_issuer_solvency_no_default_post_1971` | descriptive | Zero coded qualifying events; default/CDS/auction gates not machine-fetched. |
| WEAKENED | `welfare_transfer_us_arpa_expanded_ctc_2021` | event_study | SPM child poverty fell 4.5pp and rebounded 7.2pp; monthly CPSP and parental-LFP gates not loaded. |
| PARTIAL | `australia_hawke_keating_reform_long_run` | panel_fe | Coefficient -0.0170, p≈0.55. |
| PARTIAL | `demo_ageing_pension_burden_cross_country` | panel_fe | Coefficient +0.0913, p≈0.172. |
| PARTIAL | `demo_brazil_demographic_transition_inequality` | panel_fe_decomposition | Coefficient +1.172, p≈0.208. |
| PARTIAL | `demo_life_expectancy_lfp_panel` | panel_fe | Coefficient -0.4826, p≈0.331. |
| PARTIAL | `developmentalist_growth_premium_low_income_only` | panel_fe | Coefficient +0.1632, p≈0.688. |
| PARTIAL | `export_openness_agricultural_diversification` | panel_fe | Coefficient -2.498, p≈0.691. |
| PARTIAL | `india_extra_aadhaar_upi_productivity` | descriptive | IND account ownership rose 42.3pp; peer differential 15.8pp. |
| PARTIAL | `market_reform_duration_growth_persistence` | event_study | TWFE coefficient +0.3555, p≈0.172. |
| PARTIAL | `minimum_wage_youth_unemployment_tradeoff` | panel_fe | Coefficient -0.0919, p≈0.331. |
| PARTIAL | `monopoly_capital_concentration_markup_link` | panel_fe | Coefficient -88.78, p≈0.495. |
| PARTIAL | `quality_adjusted_consumption_market_liberal_panel` | panel_fe | Coefficient -0.0334, p≈0.189. |
| PARTIAL | `resource_developmentalism_rent_seeking_trap` | panel_fe | Coefficient -0.0081, p≈0.758. |
| PARTIAL | `startup_density_frontier_prosperity` | panel_fe | Coefficient +4.02e-06, p≈0.121. |
| PARTIAL | `tax_inequality_brazil_tax_base_evolution` | panel_fe_decomposition | Coefficient -0.7659, p≈0.048; claim direction not auto-inferred. |
| PARTIAL | `welfare_state_market_flexibility_complement` | panel_fe | Effect magnitude effectively zero. |
| PARTIAL | `wto_accession_productivity_spillover_panel` | event_study | TWFE coefficient effectively zero, p≈0.587. |

## Not ready

These modified runs are still `INCONCLUSIVE_DATA_PENDING` and should not be described as graduated unless repaired in a later batch:

`austrian_monetary_expansion_asset_bubble_not_cpi_panel`, `child_benefit_expansion_child_poverty_effect`, `china_soe_vs_cee_privatised_growth`, `chips_act_2022_semiconductor_capacity_2024_2027`, `competition_enforcement_consumer_welfare_effect`, `consumer_choice_variety_trade_market_reform`, `corbyn_manifesto_capital_flight_prediction`, `demo_canada_points_system_immigration`, `demo_germany_gastarbeiter_long_run`, `fed_2022_rate_cycle_inflation_response_lag`, `fed_qt_balance_sheet_unwind_2022_2025_market_response`, `friedman_schwartz_great_depression_monetary_cause`, `gfc_balance_sheet_recession_post_2008_household_dual_mandate`, `global_value_chain_participation_upgrade`, `great_depression_over_accumulation_vs_monetary_cause`, `high_income_escape_market_openness_1950_2024`, `interest_rate_hike_distributional_upward_redistribution`, `labour_reform_canada_1990s_ui_reform_nairu`, `labour_reform_nz_employment_contracts_act_1991`, `labour_reform_schroeder_agenda_2010_long_run_inequality`, `labour_reform_sweden_1990s_employment_recovery`, `labour_reform_uk_thatcher_union_law_1980s`, `macron_labour_tax_employment_distribution`, `mena_egypt_floatation_episodes_2016_2024`, `mena_turkey_akp_two_phase_economic_arc_2003_2024`, `oecd_product_market_deregulation_tfp_panel`, `post_covid_inflation_episode_supply_vs_demand_decomposition`, `price_controls_produce_shortages_and_quality_degradation`, `productivity_compensation_decoupling_post_1973`, `singapore_cpf_institutional_complementarity`, `tax_inequality_chile_post_pinochet_progressivity`, `tax_inequality_china_vat_reform_2016`, `tax_inequality_estonia_1994_flat_tax_dividend_reform`, `tax_inequality_france_1981_wealth_tax_top_share`, `tax_inequality_india_gst_2017_distributional`, `tax_inequality_japan_consumption_tax_hikes`, `tax_inequality_korea_progressive_turn_2017_2020`, `tax_inequality_south_africa_property_tax_burden`, `uk_real_wage_stagnation_2008_present_decomposition`, `wealth_tax_capital_flight_revenue_yield_gap`, `welfare_pension_mexico_universal_2023_fiscal_effect`, `welfare_reform_new_zealand_1991_benefit_cuts_effect`, `welfare_reform_uk_universal_credit_employment_effect`, `welfare_transfer_china_dibao_rural_pension_2009`, `welfare_transfer_finland_basic_income_experiment_2017`, `welfare_transfer_hong_kong_cash_payout_2020`, `welfare_transfer_indonesia_pkh_blt_2007_2022`, `welfare_transfer_kenya_hsnp_2015_consumption_smoothing`, `zimbabwe_land_reform_cause_decomposition`.

## Commit hygiene note

The ready hypothesis set is mixed with unrelated or separable work:

- movement-position backfill files under `movements/`
- data fetch manifests under `data/manifests/`
- entity/foundation service planning docs
- resource-developmentalism audits and agent briefs
- runner changes in `scripts/run_panel_fe.py`, `scripts/run_descriptive.py`, `scripts/run_event_study.py`, `scripts/run_local_projections.py`
- hypothesis YAML sharpening files

Recommended commit split:

1. `movement-position-backfill`: `movements/*` plus `scripts/backfill_movement_positions.py`.
2. `data-manifests-and-fetchers`: `data/manifests/*`, `scripts/build_*_vintage.py`, `data/fetchers/pwt.py`.
3. `hypothesis-graduation-runners`: runner changes and the ready `engine/runs/*` artifacts.
4. `graduation-audits`: batch/audit markdown files, including this ledger.
5. `planning-docs`: entity/foundation service docs.
