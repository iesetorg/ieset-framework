# Second-order Data Source Index

Generated from `data/second_order/source_inventory.yaml` and `data/second_order/ingestion_queue.yaml`.

## Gate Backlog Snapshot

- Strict held public claim links: 4720
- Strict eligible public claim links: 19
- Held hypotheses: 620
- Policies missing explicit designs: 3169
- Policies needing treated/comparison unit coding: 3169
- Policies needing exact event dates: 1208

## Summary

- Sources indexed: 26
- Ingestion waves: 8
- Acquisition statuses: `{"partial_ready": 16, "proprietary_gap": 1, "ready": 3, "restricted_access": 3, "scrape_needed": 3}`
- Verification statuses: `{"endpoint_verified": 4, "scout_reported_unverified": 1, "seed_unverified_url": 1, "seed_verified_official_page": 20}`
- Ingestion difficulty: `{"high": 8, "low": 7, "medium": 11}`

## Most Covered Layers

- `distributional_incidence` (13)
- `net_welfare` (10)
- `behavioral_response` (8)
- `implementation_capacity` (8)
- `allocation_distortion` (7)
- `market_structure_response` (7)
- `dynamic_investment_response` (6)
- `quality_margin` (6)
- `first_order_policy_effect` (5)
- `fiscal_or_enforcement_cost` (5)
- `first_order_price_or_transfer` (4)
- `leakage_or_substitution` (4)
- `macro_feedback` (4)
- `second_order_supply_response` (3)
- `externality_or_spillover` (2)

## Ingestion Waves

| wave | status | lane | loop | sources | target layers |
| --- | --- | --- | --- | ---: | --- |
| `treatment_contracts_backfill_v0` | schema_design_ready | treatment_contract_swarm | scout | 2 | first_order_policy_effect, first_order_price_or_transfer, implementation_capacity |
| `household_distribution_spine_v0` | research_pending | distributional_microdata_swarm | restricted_access | 6 | distributional_incidence, behavioral_response, fiscal_or_enforcement_cost, net_welfare |
| `labor_payroll_spine_v0` | ready_for_fetcher_design | labor_payroll_swarm | fetcher_design | 3 | behavioral_response, distributional_incidence, allocation_distortion, net_welfare |
| `welfare_ledger_v0` | schema_design_ready | welfare_accounting_swarm | normalization | 7 | net_welfare, distributional_incidence, fiscal_or_enforcement_cost, allocation_distortion, ... |
| `trade_procurement_firm_fast_lane_v0` | ready_for_fetcher_design | trade_procurement_firm_swarm | fetcher_design | 7 | first_order_policy_effect, leakage_or_substitution, market_structure_response, dynamic_investment_response, ... |
| `energy_reliability_outage_v0` | ready_for_fetcher_design | energy_reliability_swarm | fetcher_design | 2 | second_order_supply_response, quality_margin, implementation_capacity, dynamic_investment_response, ... |
| `city_housing_control_stack_v0` | in_progress | city_housing_control_swarm | normalization | 4 | first_order_price_or_transfer, second_order_supply_response, quality_margin, allocation_distortion, ... |
| `retail_scarcity_price_control_v0` | research_pending | retail_scarcity_swarm | scout | 4 | first_order_price_or_transfer, leakage_or_substitution, quality_margin, net_welfare, ... |

## Top Ingestion Candidates

| rank | source | family | status | difficulty | primary unlock |
| ---: | --- | --- | --- | --- | --- |
| 1 | `ieset_policy_event_treatment_contracts` | `policy_event_treatment_registry` | partial_ready | high | Defines treatment timing and unit splits for event studies, DiD, border comparisons, and triple differences. |
| 2 | `euromod_eu_silc_hbs_spine` | `household_distributional_microdata` | restricted_access | high | Measures incidence and tax-benefit channels for fiscal, welfare, labor, and energy policies. |
| 3 | `lis_lws_harmonized_microdata` | `household_distributional_microdata` | restricted_access | high | Gives cross-national incidence and household distributional measures where national microdata are hard to harmonize. |
| 4 | `ceq_fiscal_redistribution_data_center` | `household_distributional_microdata` | partial_ready | medium | Directly measures fiscal incidence for tax, transfer, subsidy, and welfare architecture tests. |
| 5 | `world_bank_lsms_microdata` | `household_distributional_microdata` | partial_ready | medium | Supplies household welfare and consumption incidence for non-OECD policy tests. |
| 6 | `ipums_cps_acs_sipp_cex_irs_spine` | `household_distributional_microdata` | partial_ready | medium | Fastest US incidence spine for tax, welfare, labor, housing, and inflation burden tests. |
| 7 | `bls_qcew_downloadable_files` | `labour_market_admin_payroll_panel` | partial_ready | low | Measures employment and wage responses for labor, tax, wage, sectoral, and local policy tests. |
| 8 | `census_lehd_qwi_j2j` | `labour_market_admin_payroll_panel` | partial_ready | medium | Measures job flows and earnings dynamics around tax, wage, welfare, migration, and labor-law treatments. |
| 9 | `ilostat_global_labor_indicators` | `labour_market_admin_payroll_panel` | partial_ready | medium | Gives global labor response coverage for hypotheses outside US/EU microdata. |
| 10 | `oecd_global_revenue_statistics` | `fiscal_tax_admin_compliance_panel` | partial_ready | medium | Provides public tax-structure backbone for fiscal cost and tax mix tests. |
| 11 | `wid_distributional_national_accounts` | `household_distributional_microdata` | partial_ready | low | Provides public distributional aggregates where microdata access is delayed. |
| 12 | `ocds_open_contracting` | `public_procurement_contract_microdata` | scrape_needed | high | Measures industrial policy targeting, fiscal cost, procurement concentration, and implementation capacity. |
| 13 | `eu_ted_procurement_notices` | `public_procurement_contract_microdata` | scrape_needed | high | High-coverage procurement layer for EU industrial policy, public spending, and competition tests. |
| 14 | `wits_trade_tariff_api` | `trade_customs_product_panel` | ready | low | Fastest ready source for trade leakage, substitution, industrial policy, and tariff tests. |
| 15 | `un_comtrade_plus` | `trade_customs_product_panel` | ready | low | Complements WITS for product-level trade flows and leakage checks. |
| 16 | `unctadstat_trade_development` | `trade_customs_product_panel` | ready | low | Adds country-level trade and development indicators around product-level WITS/Comtrade panels. |
| 17 | `world_bank_enterprise_surveys` | `firm_entry_exit_balance_sheet_panel` | partial_ready | medium | Measures firm constraints, productivity proxies, and investment responses in non-OECD policy cases. |
| 18 | `eu_klems_intanprod_productivity` | `firm_entry_exit_balance_sheet_panel` | partial_ready | medium | Adds sector productivity response to competition, regulation, trade, and industrial-policy tests. |
| 19 | `eia_open_data_energy_reliability` | `energy_reliability_outage_operator_data` | partial_ready | medium | Measures reliability, stocks, price, and supply response for energy price controls and transition policies. |
| 20 | `entso_e_transparency_platform` | `energy_reliability_outage_operator_data` | restricted_access | high | European grid reliability and price layer for nuclear, renewable, price-cap, and industrial electricity tests. |
| 21 | `zillow_research_rent_data` | `city_rent_affordability_panel` | partial_ready | low | First-order rent and market tightness layer for US rent-control and housing-supply event studies. |
| 22 | `us_census_building_permits_survey` | `national_building_permits_completions` | partial_ready | low | Supply-response layer for rent control, zoning, and local housing policy tests. |
| 23 | `nyc_open_data_housing_quality_bundle` | `city_housing_code_violation_inspection_panel` | partial_ready | medium | Quality and enforcement layer for NYC rent stabilization and tenant-protection cases. |
| 24 | `kilts_retail_scanner_datasets` | `retail_scanner_price_quantity_panel` | proprietary_gap | high | Measures controlled versus uncontrolled categories, substitution, shrinkflation, and quantity response. |
| 25 | `official_price_schedule_registry` | `official_price_schedule_control_registry` | scrape_needed | high | Defines capped versus uncapped goods for controlled category tests. |
| 26 | `dolartoday_bcv_hanke_parallel_prices` | `parallel_market_black_market_prices` | partial_ready | medium | Measures black-market leakage and hidden inflation under price and exchange controls. |
