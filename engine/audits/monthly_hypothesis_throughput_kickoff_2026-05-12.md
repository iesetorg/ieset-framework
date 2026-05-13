# Monthly Hypothesis Throughput Kickoff

Date: 2026-05-12

Purpose: restart the monthly hypothesis throughput plan with a concrete runnable batch, repair repeatability issues, and separate verdict-bearing results from data-pending claims.

## Summary

- Runs attempted today: 39
- Verdict-bearing results: 31
- Data-pending / inconclusive preflight results: 8
- Supported: 8
- Partial: 20
- Refuted: 3
- Inconclusive data-pending: 8

## Repairs Made

Several reusable `replication.py` wrappers under `engine/runs/*/` were not repeatable from the run directory because they imported `scripts.run_panel_fe`, which is shadowed on this machine by an installed third-party `scripts` package. The affected wrappers now add the repository `scripts/` directory directly to `sys.path` and import `run_panel_fe`.

This repaired the market-order panel family and unlocked the capital-account, fiscal, public-debt, government-consumption, and government-effectiveness waves below.

Follow-up hygiene pass: 65 older direct-import panel wrappers were updated the same way so future daily waves do not fail for import-path reasons.

## Wave 1: Previously Filled Data-Gap Candidates

| Hypothesis | Result |
| --- | --- |
| `industrial_concentration_labour_share_link` | inconclusive data-pending |
| `us_eu_gdp_per_capita_divergence_policy_causes` | partial |
| `federal_minimum_wage_employment_meta` | inconclusive data-pending |
| `oecd_minimum_wage_bite_low_education_unemployment` | partial |
| `us_qcew_county_food_service_minimum_wage_panel` | supported |
| `china_renewables_global_learning_curve_spillover` | refuted |
| `ira_2022_clean_energy_investment_decomposition` | inconclusive data-pending |
| `financial_negative_rates_eurozone_2014_2022` | inconclusive data-pending |
| `eurozone_austerity_distributional_incidence` | inconclusive data-pending |
| `child_benefit_expansion_child_poverty_effect` | inconclusive data-pending |

Wave 1 tally: 1 supported, 2 partial, 1 refuted, 6 inconclusive.

## Wave 2: Capital-Account / Openness Equivalents

The exact first-ten IDs in `new_data_gap_unlocks_and_first50_2026-05-06.md` are launch candidates, not yet promoted specs. Existing promoted equivalents were run instead to avoid duplicate IDs while still advancing the same policy track.

| Hypothesis | Result |
| --- | --- |
| `latam_extra_capital_account_openness_panel_1990_2024` | partial |
| `liberal_capital_account_openness_growth_premium_panel` | partial |
| `capital_account_openness_institutional_threshold` | partial |
| `market_order_capital_account_openness_fdi_inflows_share_panel` | partial |
| `market_order_capital_account_openness_gdp_pc_growth_panel` | supported |
| `market_order_capital_account_openness_high_tech_exports_panel` | partial |
| `market_order_capital_account_openness_private_investment_share_panel` | refuted |

Wave 2 tally: 1 supported, 5 partial, 1 refuted.

## Wave 3: Market-Order Macro Panel Family

| Hypothesis | Result |
| --- | --- |
| `market_order_fiscal_balance_gdp_pc_growth_panel` | supported |
| `market_order_fiscal_balance_private_investment_share_panel` | supported |
| `market_order_fiscal_balance_gross_savings_share_panel` | supported |
| `market_order_fiscal_balance_private_credit_depth_panel` | refuted |
| `market_order_public_debt_gdp_pc_growth_panel` | partial |
| `market_order_public_debt_private_investment_share_panel` | supported |
| `market_order_public_debt_gross_savings_share_panel` | partial |
| `market_order_public_debt_private_credit_depth_panel` | partial |
| `market_order_government_consumption_gdp_pc_growth_panel` | supported |
| `market_order_government_consumption_private_investment_share_panel` | partial |
| `market_order_government_consumption_gross_savings_share_panel` | supported |
| `market_order_government_consumption_manufacturing_share_panel` | partial |
| `market_order_government_effectiveness_gdp_pc_growth_panel` | partial |
| `market_order_government_effectiveness_private_investment_share_panel` | partial |
| `market_order_government_effectiveness_gross_savings_share_panel` | partial |
| `market_order_government_effectiveness_manufacturing_share_panel` | partial |

Wave 3 tally: 6 supported, 9 partial, 1 refuted.

## Wave 4: Next Queue Smoke Run

| Hypothesis | Result |
| --- | --- |
| `oecd_product_market_deregulation_tfp_panel` | inconclusive data-pending |
| `unemployment_benefit_generosity_employment_drag` | partial |
| `government_spending_tfp_drag_panel` | partial |
| `flat_tax_reform_growth_panel` | partial |
| `mortgage_market_liberalisation_homeownership_panel` | partial |
| `privatisation_transition_tfp_panel` | inconclusive data-pending |

Wave 4 tally: 0 supported, 4 partial, 0 refuted, 2 inconclusive.

## Throughput Strategy From Here

1. Keep daily batches to 20-40 attempted runs unless the family is highly templated and already validated.
2. Count only supported, partial, and refuted as verdict-bearing throughput; keep inconclusive runs visible but outside scoreboard movement until data gaps are repaired.
3. Prefer promoted equivalent specs over creating duplicate IDs when a launch candidate overlaps an existing hypothesis.
4. After each wave, run validations and update a dated audit file before mapping anything to the scoreboard.
5. Next best batch: promoted OECD/WDI/Eurostat market-order panels already using common runners, followed by the unpromoted first-50 launch candidates that need YAML promotion.

## Immediate Next Queue

- Repair data/model issues exposed by Wave 4:
  - `oecd_product_market_deregulation_tfp_panel`: treatment has no within-country variation under the current fixed-effects design.
  - `privatisation_transition_tfp_panel`: mass-privatisation indicator has no within-country variation under the current fixed-effects design.
- Promote exact first-50 launch candidates where no equivalent spec exists:
  - exchange-rate regime volatility and crisis-cost claims
  - inflation / monetary expansion asset-price claims
  - housing asset inflation and credit-cycle claims
  - top-income-share and market-openness claims
