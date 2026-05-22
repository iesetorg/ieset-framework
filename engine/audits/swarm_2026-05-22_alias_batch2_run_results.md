# Swarm 2026-05-22 NEEDS_ALIAS Batch 2 Run Results

This audit records the first-pass generic `panel_fe` execution of the 27 remaining promoted alias-repair candidates.

These are triage verdicts only: no scoreboard mappings or claim links were added in this pass.

## Summary

- hypotheses attempted: 27
- diagnostics written: 27
- supported: 10
- refuted: 7
- partial: 10
- inconclusive_data_pending: 0
- alias repair: `job_guarantee_almp_unemployment_floor_panel` now uses the local OECD SOCX aggregate ALMP programme slice
- alias repair: `capacity_transport_infrastructure_market_access_productivity` uses rail passenger-km after the local road-density vintage had blank country codes
- runner repair: schema country-group filters now preserve group tokens such as `EU` before ISO2 normalization

## Topic By Verdict

| topic | supported | refuted | partial | inconclusive | total |
| --- | ---: | ---: | ---: | ---: | ---: |
| energy | 1 | 0 | 3 | 0 | 4 |
| fiscal | 2 | 1 | 2 | 0 | 5 |
| growth | 1 | 2 | 1 | 0 | 4 |
| healthcare | 1 | 1 | 0 | 0 | 2 |
| housing | 0 | 0 | 2 | 0 | 2 |
| institutional_quality | 1 | 0 | 0 | 0 | 1 |
| labour | 1 | 2 | 2 | 0 | 5 |
| monetary | 3 | 0 | 0 | 0 | 3 |
| trade | 0 | 1 | 0 | 0 | 1 |

## Verdict Inventory

| hypothesis | topic | verdict | reason |
| --- | --- | --- | --- |
| `ml_fuel_subsidy_reform_targeted_transfer_qol` | energy | SUPPORTED | coef=+2.466e-11 (sign matches claim +), p=0.0556 |
| `deficits_private_saving_sectoral_balance_panel` | fiscal | SUPPORTED | coef=+0.8249 (sign matches claim +), p=0 |
| `eurostat_interest_spending_public_investment_tradeoff_panel` | fiscal | SUPPORTED | coef=-0.05885 (sign matches claim -), p=2.5e-07 |
| `ml_directed_credit_capital_misallocation_growth_drag` | growth | SUPPORTED | coef=-0.001099 (sign matches claim -), p=0.00632 |
| `capacity_water_sanitation_urbanization_health_dividend` | healthcare | SUPPORTED | coef=-0.8477 (sign matches claim -), p=0 |
| `ml_contract_enforcement_firm_scale_productivity` | institutional_quality | SUPPORTED | coef=+0.1269 (sign matches claim +), p=0.00022 |
| `capacity_unemployment_benefits_activation_threshold` | labour | SUPPORTED | coef=-1.607 (sign matches claim -), p=3.46e-06 |
| `capacity_bank_capital_buffers_credit_cycle_cost` | monetary | SUPPORTED | coef=-0.03133 (sign matches claim -), p=1.16e-08 |
| `central_bank_asset_purchases_yields_inflation_panel` | monetary | SUPPORTED | coef=+0.5035 (sign matches claim +), p=0.000521 |
| `sovereign_currency_debt_inflation_threshold_panel` | monetary | SUPPORTED | coef=+0.126 (sign matches claim +), p=0.00699 |
| `capacity_gfc_stimulus_speed_output_recovery` | fiscal | REFUTED | coef=-0.1062 (sign opposite claim +), p=0.0299 |
| `ml_ip_protection_moderate_strength_innovation_diffusion` | growth | REFUTED | coef=-2.875e-07 (sign opposite claim +), p=1.7e-09 |
| `oecd_ict_sector_productivity_spillover_panel` | growth | REFUTED | coef=-0.04359 (sign opposite claim +), p=7.92e-06 |
| `capacity_health_insurance_labour_market_complement` | healthcare | REFUTED | coef=-0.1534 (sign opposite claim +), p=0.0602 |
| `job_guarantee_almp_unemployment_floor_panel` | labour | REFUTED | coef=+0.7581 (sign opposite claim -), p=0.0882 |
| `oecd_vocational_track_youth_unemployment_panel` | labour | REFUTED | coef=+0.6612 (sign opposite claim -), p=0.053 |
| `food_production_trade_openness_resilience_panel` | trade | REFUTED | coef=+0.5794 (sign opposite claim -), p=0.0745 |
| `capacity_energy_shock_transfers_vs_price_controls` | energy | PARTIAL | coef=+5.258e-11, p=0.417 (above α=0.1); direction inconclusive |
| `capacity_green_industrial_policy_electricity_price_tradeoff` | energy | PARTIAL | coef=-0.007584, p=0.569 (above α=0.1); direction inconclusive |
| `ml_energy_price_controls_shortage_fiscal_burden` | energy | PARTIAL | coef=-1.272e-11, p=0.152 (above α=0.1); direction inconclusive |
| `education_spending_inequality_mobility_panel` | fiscal | PARTIAL | coef=-0.3724, p=0.134 (above α=0.1); direction inconclusive |
| `ml_consumption_tax_shift_savings_investment_longrun` | fiscal | PARTIAL | coef=+0.01529, p=0.654 (above α=0.1); direction inconclusive |
| `capacity_transport_infrastructure_market_access_productivity` | growth | PARTIAL | coef=+1.039e-07, p=0.957 (above α=0.1); direction inconclusive |
| `capacity_housing_supply_credit_boom_amplifier` | housing | PARTIAL | coef=+0.1132, p=0.346 (above α=0.1); direction inconclusive |
| `eurostat_construction_supply_housing_cost_relief_panel` | housing | PARTIAL | coef=+0.0005027, p=0.284 (above α=0.1); direction inconclusive |
| `capacity_childcare_spending_female_lfp_housing_cost` | labour | PARTIAL | coef=+1.505, p=0.309 (above α=0.1); direction inconclusive |
| `capacity_in_work_benefits_cliff_employment` | labour | PARTIAL | coef=-0.4625, p=0.221 (above α=0.1); direction inconclusive |
