# Ready No-Run Pre-Registration Wave - 2026-05-03

## Methodology Gate

- These specs were candidate-stage, schema-valid, and had no existing `engine/runs/<id>` directory.
- Only specs with a loadable outcome and treatment were promoted to `pre_registered`.
- Stale `covers_claims` were removed because their reciprocal position indexes were invalid; these are hypothesis runs, not school-scoreboard mappings yet.
- Run artifacts must be created only after this pre-registration commit.

## Runnable Count: 7

- `flat_tax_reform_growth_panel`
- `government_spending_tfp_drag_panel`
- `mortgage_market_liberalisation_homeownership_panel`
- `privatisation_transition_tfp_panel`
- `oecd_product_market_deregulation_tfp_panel`
- `unemployment_benefit_generosity_employment_drag`
- `workfare_conditionality_employment_effect`

## Blocked Count: 4

- `electricity_market_unbundling_price_reliability_panel`: no loadable outcome variable
- `capital_gains_tax_cut_investment_response_panel`: no loadable/constructible treatment variable
- `minimum_wage_youth_unemployment_tradeoff`: no loadable/constructible treatment variable
- `bilateral_investment_treaty_fdi_panel`: no loadable/constructible treatment variable
