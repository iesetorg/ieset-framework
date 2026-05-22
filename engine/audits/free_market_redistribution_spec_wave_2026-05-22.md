# Free-Market / Redistribution Hypothesis Spec Wave - 2026-05-22

## Summary

Generated 32 fresh candidate hypothesis specs and matching steelman files. The
wave targets market-dynamism mechanisms and redistribution/state-allocation
claims without pre-assigning verdicts or scoreboard links.

## Validation

- Targeted schema validation for the 32 new specs: pass.
- Runnability audit after the wave: 1,657 total specs, 1,575 READY, 82 NEEDS_DATA,
  0 NEEDS_TEMPLATE, 0 LEGACY_SCHEMA.
- New-wave runnability: 32/32 READY under the current publisher-level audit.
- New-wave series-level caveat: 14/32 specs still have exact-series gaps that
  should be repaired before clean replication.
- No `covers_claims` links were added in this wave; scoreboard mapping should be
  a separate review pass after specs are tested or deliberately pre-registered.

## Topic Split

| Topic | Count |
| --- | ---: |
| growth | 8 |
| fiscal | 4 |
| distribution | 4 |
| labour | 4 |
| welfare_architecture | 4 |
| trade | 2 |
| housing | 2 |
| energy | 2 |
| institutional_quality | 2 |

## Spec Groups

### Market Dynamism / Growth

- `market_dynamism_property_rights_investment_growth`
- `market_dynamism_private_credit_productivity_growth`
- `market_dynamism_entrepreneurial_entry_income_growth`
- `market_dynamism_tariff_reduction_consumption_pc`
- `market_dynamism_export_diversification_growth`
- `market_dynamism_government_consumption_investment_drag`
- `market_dynamism_regulatory_freedom_hightech_exports`
- `market_dynamism_investment_freedom_renewables_diffusion`

### Redistribution / Tax / Distribution

- `redistribution_tax_private_investment_drag_panel`
- `redistribution_progressive_tax_growth_threshold_oecd`
- `redistribution_transfer_work_incentive_lfpr_oecd`
- `redistribution_public_consumption_tfp_drag_pwt_panel`
- `redistribution_market_income_growth_poverty_exit_panel`
- `redistribution_tax_transfer_mobility_oecd`
- `redistribution_gini_compression_median_income_growth_oecd`
- `redistribution_social_spending_bottom40_growth_panel`

### Labour / Welfare Work Incentives

- `oecd_tax_wedge_low_wage_employment_penalty`
- `oecd_bargaining_extension_youth_entry_penalty`
- `business_freedom_employer_entry_employment_panel`
- `temporary_contract_restrictions_youth_hiring_panel`
- `oecd_taxben_benefit_cliff_lfp_penalty`
- `in_work_benefits_low_income_employment_panel`
- `activation_sanctions_reemployment_duration_panel`
- `unconditional_transfer_work_hours_response_panel`

### Trade / Housing / Energy / Institutions

- `trade_openness_patent_diffusion_panel`
- `state_trade_barriers_consumption_variety_panel`
- `rent_price_controls_building_permits_eu_panel`
- `construction_permit_burden_housing_output_panel`
- `energy_market_competition_renewable_capacity_panel`
- `price_control_intensity_electricity_access_growth_panel`
- `state_allocation_private_credit_innovation_panel`
- `price_signal_freedom_inflation_volatility_panel`

## Immediate Run Queue

The cleanest first-pass candidates, because their source aliases are already
mostly local and broad-panel friendly:

1. `market_dynamism_property_rights_investment_growth`
2. `market_dynamism_private_credit_productivity_growth`
3. `market_dynamism_tariff_reduction_consumption_pc`
4. `market_dynamism_export_diversification_growth`
5. `market_dynamism_government_consumption_investment_drag`
6. `market_dynamism_investment_freedom_renewables_diffusion`
7. `redistribution_tax_private_investment_drag_panel`
8. `redistribution_progressive_tax_growth_threshold_oecd`
9. `redistribution_public_consumption_tfp_drag_pwt_panel`
10. `redistribution_market_income_growth_poverty_exit_panel`
11. `energy_market_competition_renewable_capacity_panel`
12. `price_control_intensity_electricity_access_growth_panel`
13. `trade_openness_patent_diffusion_panel`
14. `state_allocation_private_credit_innovation_panel`
15. `price_signal_freedom_inflation_volatility_panel`

## Series-Gap Repair Queue

These are valid specs but need exact-series alias/data work before a clean run:

- OECD TaxBEN and Benefits/Wages aliases for benefit cliffs, participation tax
  rates, replacement rates, and sanction/job-search rules.
- ILOSTAT education/age employment-rate cells and unemployment-duration cells.
- OECD collective-bargaining extension and EPL temporary-contract aliases.
- Housing/construction panels needing Eurostat building-permit/rent-burden or
  WDI construction-permit series.
- Mobility and distribution panels needing OWID/OECD mobility and bottom-income
  share harmonisation.
- Trade variety panel needing WITS import-concentration or a local concentration
  alias.

## Methodology Note

This wave intentionally frames free-market and redistribution claims as
falsifiable empirical predictions. A supported result can become evidence for
market-process claims and against redistribution/state-allocation claims only
after replication, evidence-packet review, and a separate claim-mapping pass.
