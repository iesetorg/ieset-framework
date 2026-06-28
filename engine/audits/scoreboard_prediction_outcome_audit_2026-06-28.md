# Scoreboard Prediction-Outcome Audit

Generated: 2026-06-28

## Methodology Gate

- School outcomes are computed from `verdict + school_prediction + polarity`.
- Raw `empirical_status` is a hypothesis-verdict label, not automatically a school win.
- `SUPPORTED` refutes a school that predicted `falsified`; `REFUTED` supports that school.
- Directional partials count half-weight; neutral partials do not move net score.
- Tiny aggregate margins are a no-call: `abs(net) <= max(5, 5% of tested)` is `too_close_to_call`.
- The audit keeps a separate signed lean so no-call rows still show whether the net is positive, negative, or flat.
- Q-net discounts lower-identification evidence: causal=1.0, associational=0.5, descriptive/canonical=0.25.
- Benchmark-control rows are computed for calibration but excluded from ranked school outcomes.

## Ranked School Outcomes

| school | lean | q-net | q-band | raw net | decisive net | tested | supports | partial + | partial - | refutes | neutral | untested |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `chicago_monetarism` | positive_lean | 25.4 | ±7.7 | 45.0 | 29 | 282 | 67 | 33 | 1 | 38 | 143 | 11 |
| `classical_liberal` | positive_lean | 22.6 | ±8.9 | 38.5 | 26 | 327 | 82 | 26 | 1 | 56 | 162 | 13 |
| `austrian` | positive_lean | 18.9 | ±7.8 | 33.5 | 20 | 278 | 61 | 27 | 0 | 41 | 149 | 9 |
| `ordoliberal` | positive_lean | 16.4 | ±8.2 | 27.5 | 15 | 295 | 60 | 25 | 0 | 45 | 165 | 11 |
| `developmentalism` | positive_lean | 10.0 | ±7.5 | 39.5 | 36 | 287 | 69 | 8 | 1 | 33 | 176 | 9 |
| `new_keynesian` | positive_lean | 3.2 | ±7.3 | 10.5 | 3 | 271 | 23 | 15 | 0 | 20 | 213 | 10 |
| `marxist_leninist` | flat | 0.0 | ±7.1 | 8.0 | 9 | 263 | 35 | 18 | 20 | 26 | 164 | 15 |
| `institutionalism` | negative_lean | -0.1 | ±7.6 | 3.0 | -2 | 275 | 30 | 11 | 1 | 32 | 201 | 12 |
| `marxian` | negative_lean | -2.8 | ±7.2 | 0.0 | 0 | 270 | 46 | 18 | 18 | 46 | 142 | 13 |
| `mmt` | negative_lean | -4.0 | ±7.1 | -0.5 | 3 | 267 | 46 | 11 | 18 | 43 | 149 | 12 |
| `post_keynesian` | negative_lean | -4.4 | ±7.4 | -1.0 | 2 | 270 | 56 | 13 | 19 | 54 | 128 | 11 |
| `eco_socialist` | negative_lean | -5.5 | ±7.2 | -1.5 | -1 | 272 | 48 | 17 | 18 | 49 | 140 | 15 |
| `degrowth` | negative_lean | -5.6 | ±7.1 | -5.0 | -3 | 268 | 28 | 14 | 18 | 31 | 177 | 13 |
| `social_democratic` | negative_lean | -5.8 | ±7.8 | -3.5 | -3 | 287 | 58 | 18 | 19 | 61 | 131 | 9 |
| `market_socialist` | negative_lean | -6.0 | ±7.1 | -3.5 | -3 | 267 | 50 | 17 | 18 | 53 | 129 | 14 |
| `democratic_socialist` | negative_lean | -6.5 | ±7.2 | -4.0 | -4 | 268 | 51 | 19 | 19 | 55 | 124 | 14 |

## Benchmark Control Readout

These rows are calibration/house-position controls. They are not ranked as ideological schools.

| control | lean | q-net | q-band | raw net | decisive net | tested | supports | partial + | partial - | refutes | neutral | untested |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `empirical_pragmatist` | positive_lean | 9.8 | ±8.1 | 19.0 | 15 | 292 | 36 | 9 | 1 | 21 | 225 | 8 |

## Raw-Status Misread Risks

These are claims where the raw `empirical_status` label points the opposite way from the school-level scoreboard outcome.

| school | claim | hypothesis | raw status | prediction | outcome |
| --- | ---: | --- | --- | --- | --- |
| `austrian` | 161 | `renewable_share_electricity_price_transition_cost_panel` | supported | falsified | refutes_position |
| `austrian` | 179 | `deficits_private_saving_sectoral_balance_panel` | supported | falsified | refutes_position |
| `austrian` | 185 | `governance_rnd_hightech_return_panel` | supported | falsified | refutes_position |
| `austrian` | 196 | `oecd_socx_poverty_reduction_per_spending_point_panel` | supported | falsified | refutes_position |
| `austrian` | 206 | `wdi_out_of_pocket_health_spending_mortality_panel` | supported | falsified | refutes_position |
| `austrian` | 265 | `central_bank_asset_purchases_yields_inflation_panel` | supported | falsified | refutes_position |
| `austrian` | 270 | `sovereign_currency_debt_inflation_threshold_panel` | supported | falsified | refutes_position |
| `austrian` | 276 | `industrial_policy_hightech_exports_patents_panel` | supported | falsified | refutes_position |
| `chicago_monetarism` | 167 | `renewable_share_electricity_price_transition_cost_panel` | supported | falsified | refutes_position |
| `chicago_monetarism` | 185 | `deficits_private_saving_sectoral_balance_panel` | supported | falsified | refutes_position |
| `chicago_monetarism` | 191 | `governance_rnd_hightech_return_panel` | supported | falsified | refutes_position |
| `chicago_monetarism` | 202 | `oecd_socx_poverty_reduction_per_spending_point_panel` | supported | falsified | refutes_position |
| `chicago_monetarism` | 212 | `wdi_out_of_pocket_health_spending_mortality_panel` | supported | falsified | refutes_position |
| `chicago_monetarism` | 271 | `central_bank_asset_purchases_yields_inflation_panel` | supported | falsified | refutes_position |
| `chicago_monetarism` | 276 | `sovereign_currency_debt_inflation_threshold_panel` | supported | falsified | refutes_position |
| `chicago_monetarism` | 282 | `industrial_policy_hightech_exports_patents_panel` | supported | falsified | refutes_position |
| `classical_liberal` | 214 | `renewable_share_electricity_price_transition_cost_panel` | supported | falsified | refutes_position |
| `classical_liberal` | 232 | `deficits_private_saving_sectoral_balance_panel` | supported | falsified | refutes_position |
| `classical_liberal` | 238 | `governance_rnd_hightech_return_panel` | supported | falsified | refutes_position |
| `classical_liberal` | 249 | `oecd_socx_poverty_reduction_per_spending_point_panel` | supported | falsified | refutes_position |
| `classical_liberal` | 259 | `wdi_out_of_pocket_health_spending_mortality_panel` | supported | falsified | refutes_position |
| `classical_liberal` | 318 | `central_bank_asset_purchases_yields_inflation_panel` | supported | falsified | refutes_position |
| `classical_liberal` | 323 | `sovereign_currency_debt_inflation_threshold_panel` | supported | falsified | refutes_position |
| `classical_liberal` | 329 | `industrial_policy_hightech_exports_patents_panel` | supported | falsified | refutes_position |
| `degrowth` | 148 | `ml_fuel_subsidy_reform_targeted_transfer_qol` | supported | falsified | refutes_position |
| `degrowth` | 176 | `eurostat_interest_spending_public_investment_tradeoff_panel` | supported | falsified | refutes_position |
| `degrowth` | 182 | `ml_central_bank_independence_inflation_real_wage_panel` | supported | falsified | refutes_position |
| `degrowth` | 186 | `ml_fiscal_rule_debt_service_growth_resilience` | supported | falsified | refutes_position |
| `degrowth` | 207 | `ml_directed_credit_capital_misallocation_growth_drag` | supported | falsified | refutes_position |
| `degrowth` | 227 | `ml_contract_enforcement_firm_scale_productivity` | supported | falsified | refutes_position |
| `degrowth` | 260 | `fred_m2_asset_price_cpi_divergence_us_panel` | supported | falsified | refutes_position |
| `degrowth` | 262 | `ml_financial_repression_savings_real_rate_investment` | supported | falsified | refutes_position |
| `democratic_socialist` | 64 | `poland_market_transition_30yr_growth` | supported | falsified | refutes_position |
| `democratic_socialist` | 65 | `sweden_1990s_market_reform_recovery` | falsified | falsified | supports_position |
| `democratic_socialist` | 70 | `firm_entry_rate_long_run_productivity` | supported | falsified | refutes_position |
| `democratic_socialist` | 71 | `frontier_income_volatility_state_allocation` | falsified | falsified | supports_position |
| `democratic_socialist` | 149 | `ml_fuel_subsidy_reform_targeted_transfer_qol` | supported | falsified | refutes_position |
| `democratic_socialist` | 177 | `eurostat_interest_spending_public_investment_tradeoff_panel` | supported | falsified | refutes_position |
| `democratic_socialist` | 183 | `ml_central_bank_independence_inflation_real_wage_panel` | supported | falsified | refutes_position |
| `democratic_socialist` | 187 | `ml_fiscal_rule_debt_service_growth_resilience` | supported | falsified | refutes_position |
| `democratic_socialist` | 208 | `ml_directed_credit_capital_misallocation_growth_drag` | supported | falsified | refutes_position |
| `democratic_socialist` | 228 | `ml_contract_enforcement_firm_scale_productivity` | supported | falsified | refutes_position |
| `democratic_socialist` | 261 | `fred_m2_asset_price_cpi_divergence_us_panel` | supported | falsified | refutes_position |
| `democratic_socialist` | 263 | `ml_financial_repression_savings_real_rate_investment` | supported | falsified | refutes_position |
| `developmentalism` | 130 | `bank_state_ownership_credit_misallocation` | falsified | falsified | supports_position |
| `developmentalism` | 131 | `venture_capital_market_depth_innovation` | falsified | falsified | supports_position |
| `developmentalism` | 152 | `korea_post_chaebol_liberalisation_frontier_growth` | falsified | falsified | supports_position |
| `eco_socialist` | 154 | `ml_fuel_subsidy_reform_targeted_transfer_qol` | supported | falsified | refutes_position |
| `eco_socialist` | 182 | `eurostat_interest_spending_public_investment_tradeoff_panel` | supported | falsified | refutes_position |
| `eco_socialist` | 188 | `ml_central_bank_independence_inflation_real_wage_panel` | supported | falsified | refutes_position |
| `eco_socialist` | 192 | `ml_fiscal_rule_debt_service_growth_resilience` | supported | falsified | refutes_position |
| `eco_socialist` | 213 | `ml_directed_credit_capital_misallocation_growth_drag` | supported | falsified | refutes_position |
| `eco_socialist` | 233 | `ml_contract_enforcement_firm_scale_productivity` | supported | falsified | refutes_position |
| `eco_socialist` | 266 | `fred_m2_asset_price_cpi_divergence_us_panel` | supported | falsified | refutes_position |
| `eco_socialist` | 268 | `ml_financial_repression_savings_real_rate_investment` | supported | falsified | refutes_position |
| `market_socialist` | 138 | `bls_qcew_county_food_service_minimum_wage_growth` | supported | falsified | refutes_position |
| `market_socialist` | 148 | `ml_fuel_subsidy_reform_targeted_transfer_qol` | supported | falsified | refutes_position |
| `market_socialist` | 176 | `eurostat_interest_spending_public_investment_tradeoff_panel` | supported | falsified | refutes_position |
| `market_socialist` | 182 | `ml_central_bank_independence_inflation_real_wage_panel` | supported | falsified | refutes_position |
| `market_socialist` | 186 | `ml_fiscal_rule_debt_service_growth_resilience` | supported | falsified | refutes_position |
| `market_socialist` | 207 | `ml_directed_credit_capital_misallocation_growth_drag` | supported | falsified | refutes_position |
| `market_socialist` | 227 | `ml_contract_enforcement_firm_scale_productivity` | supported | falsified | refutes_position |
| `market_socialist` | 260 | `fred_m2_asset_price_cpi_divergence_us_panel` | supported | falsified | refutes_position |
| `market_socialist` | 262 | `ml_financial_repression_savings_real_rate_investment` | supported | falsified | refutes_position |
| `marxian` | 150 | `ml_fuel_subsidy_reform_targeted_transfer_qol` | supported | falsified | refutes_position |
| `marxian` | 178 | `eurostat_interest_spending_public_investment_tradeoff_panel` | supported | falsified | refutes_position |
| `marxian` | 184 | `ml_central_bank_independence_inflation_real_wage_panel` | supported | falsified | refutes_position |
| `marxian` | 188 | `ml_fiscal_rule_debt_service_growth_resilience` | supported | falsified | refutes_position |
| `marxian` | 209 | `ml_directed_credit_capital_misallocation_growth_drag` | supported | falsified | refutes_position |
| `marxian` | 229 | `ml_contract_enforcement_firm_scale_productivity` | supported | falsified | refutes_position |
| `marxian` | 262 | `fred_m2_asset_price_cpi_divergence_us_panel` | supported | falsified | refutes_position |
| `marxian` | 264 | `ml_financial_repression_savings_real_rate_investment` | supported | falsified | refutes_position |
| `marxist_leninist` | 63 | `poland_market_transition_30yr_growth` | supported | falsified | refutes_position |
| `marxist_leninist` | 64 | `sweden_1990s_market_reform_recovery` | falsified | falsified | supports_position |
| `marxist_leninist` | 69 | `firm_entry_rate_long_run_productivity` | supported | falsified | refutes_position |
| `marxist_leninist` | 70 | `frontier_income_volatility_state_allocation` | falsified | falsified | supports_position |
| `marxist_leninist` | 145 | `ml_fuel_subsidy_reform_targeted_transfer_qol` | supported | falsified | refutes_position |
| `marxist_leninist` | 173 | `eurostat_interest_spending_public_investment_tradeoff_panel` | supported | falsified | refutes_position |
| `marxist_leninist` | 179 | `ml_central_bank_independence_inflation_real_wage_panel` | supported | falsified | refutes_position |
| `marxist_leninist` | 183 | `ml_fiscal_rule_debt_service_growth_resilience` | supported | falsified | refutes_position |
| `marxist_leninist` | 204 | `ml_directed_credit_capital_misallocation_growth_drag` | supported | falsified | refutes_position |
| `marxist_leninist` | 224 | `ml_contract_enforcement_firm_scale_productivity` | supported | falsified | refutes_position |
| `marxist_leninist` | 257 | `fred_m2_asset_price_cpi_divergence_us_panel` | supported | falsified | refutes_position |
| `marxist_leninist` | 259 | `ml_financial_repression_savings_real_rate_investment` | supported | falsified | refutes_position |
| `mmt` | 146 | `ml_fuel_subsidy_reform_targeted_transfer_qol` | supported | falsified | refutes_position |
| `mmt` | 174 | `eurostat_interest_spending_public_investment_tradeoff_panel` | supported | falsified | refutes_position |
| `mmt` | 180 | `ml_central_bank_independence_inflation_real_wage_panel` | supported | falsified | refutes_position |
| `mmt` | 184 | `ml_fiscal_rule_debt_service_growth_resilience` | supported | falsified | refutes_position |
| `mmt` | 205 | `ml_directed_credit_capital_misallocation_growth_drag` | supported | falsified | refutes_position |
| `mmt` | 225 | `ml_contract_enforcement_firm_scale_productivity` | supported | falsified | refutes_position |
| `mmt` | 258 | `fred_m2_asset_price_cpi_divergence_us_panel` | supported | falsified | refutes_position |
| `mmt` | 260 | `ml_financial_repression_savings_real_rate_investment` | supported | falsified | refutes_position |
| `post_keynesian` | 66 | `poland_market_transition_30yr_growth` | supported | falsified | refutes_position |
| `post_keynesian` | 67 | `sweden_1990s_market_reform_recovery` | falsified | falsified | supports_position |
| `post_keynesian` | 72 | `firm_entry_rate_long_run_productivity` | supported | falsified | refutes_position |
| `post_keynesian` | 73 | `frontier_income_volatility_state_allocation` | falsified | falsified | supports_position |
| `post_keynesian` | 148 | `ml_fuel_subsidy_reform_targeted_transfer_qol` | supported | falsified | refutes_position |
| `post_keynesian` | 176 | `eurostat_interest_spending_public_investment_tradeoff_panel` | supported | falsified | refutes_position |
| `post_keynesian` | 182 | `ml_central_bank_independence_inflation_real_wage_panel` | supported | falsified | refutes_position |
| `post_keynesian` | 186 | `ml_fiscal_rule_debt_service_growth_resilience` | supported | falsified | refutes_position |
| `post_keynesian` | 207 | `ml_directed_credit_capital_misallocation_growth_drag` | supported | falsified | refutes_position |
| `post_keynesian` | 227 | `ml_contract_enforcement_firm_scale_productivity` | supported | falsified | refutes_position |
| `post_keynesian` | 260 | `fred_m2_asset_price_cpi_divergence_us_panel` | supported | falsified | refutes_position |
| `post_keynesian` | 262 | `ml_financial_repression_savings_real_rate_investment` | supported | falsified | refutes_position |
| `social_democratic` | 69 | `oecd_collective_bargaining_growth_penalty_kei` | falsified | supported | supports_position |
| `social_democratic` | 76 | `poland_market_transition_30yr_growth` | supported | falsified | refutes_position |
| `social_democratic` | 77 | `sweden_1990s_market_reform_recovery` | falsified | falsified | supports_position |
| `social_democratic` | 91 | `firm_entry_rate_long_run_productivity` | supported | falsified | refutes_position |
| `social_democratic` | 92 | `frontier_income_volatility_state_allocation` | falsified | falsified | supports_position |
| `social_democratic` | 148 | `oecd_low_education_unemployment_minimum_wage_bite` | supported | falsified | refutes_position |
| `social_democratic` | 163 | `ml_fuel_subsidy_reform_targeted_transfer_qol` | supported | falsified | refutes_position |
| `social_democratic` | 191 | `eurostat_interest_spending_public_investment_tradeoff_panel` | supported | falsified | refutes_position |
| `social_democratic` | 197 | `ml_central_bank_independence_inflation_real_wage_panel` | supported | falsified | refutes_position |
| `social_democratic` | 201 | `ml_fiscal_rule_debt_service_growth_resilience` | supported | falsified | refutes_position |
| `social_democratic` | 222 | `ml_directed_credit_capital_misallocation_growth_drag` | supported | falsified | refutes_position |
| `social_democratic` | 242 | `ml_contract_enforcement_firm_scale_productivity` | supported | falsified | refutes_position |
| `social_democratic` | 275 | `fred_m2_asset_price_cpi_divergence_us_panel` | supported | falsified | refutes_position |
| `social_democratic` | 277 | `ml_financial_repression_savings_real_rate_investment` | supported | falsified | refutes_position |

## Left-Cluster Readout

- `degrowth`: signal=too_close_to_call; lean=negative_lean; q-net=-5.6; raw-net=-5.0; q-band=±7.1; supports=28; partial+=14; partial-=18; refutes=31; neutral=177; untested=13.
- `eco_socialist`: signal=too_close_to_call; lean=negative_lean; q-net=-5.5; raw-net=-1.5; q-band=±7.2; supports=48; partial+=17; partial-=18; refutes=49; neutral=140; untested=15.
- `democratic_socialist`: signal=too_close_to_call; lean=negative_lean; q-net=-6.5; raw-net=-4.0; q-band=±7.2; supports=51; partial+=19; partial-=19; refutes=55; neutral=124; untested=14.
- `market_socialist`: signal=too_close_to_call; lean=negative_lean; q-net=-6.0; raw-net=-3.5; q-band=±7.1; supports=50; partial+=17; partial-=18; refutes=53; neutral=129; untested=14.
- `marxian`: signal=too_close_to_call; lean=negative_lean; q-net=-2.8; raw-net=0.0; q-band=±7.2; supports=46; partial+=18; partial-=18; refutes=46; neutral=142; untested=13.
- `marxist_leninist`: signal=too_close_to_call; lean=flat; q-net=0.0; raw-net=8.0; q-band=±7.1; supports=35; partial+=18; partial-=20; refutes=26; neutral=164; untested=15.
- `mmt`: signal=too_close_to_call; lean=negative_lean; q-net=-4.0; raw-net=-0.5; q-band=±7.1; supports=46; partial+=11; partial-=18; refutes=43; neutral=149; untested=12.
- `post_keynesian`: signal=too_close_to_call; lean=negative_lean; q-net=-4.4; raw-net=-1.0; q-band=±7.4; supports=56; partial+=13; partial-=19; refutes=54; neutral=128; untested=11.
- `social_democratic`: signal=too_close_to_call; lean=negative_lean; q-net=-5.8; raw-net=-3.5; q-band=±7.8; supports=58; partial+=18; partial-=19; refutes=61; neutral=131; untested=9.

## Marxist-Cluster Readout

- `marxian`: signal=too_close_to_call; q-net=-2.8; raw-net=0.0; q-band=±7.2; supports=46; partial+=18; partial-=18; refutes=46; neutral=142; untested=13.
- `marxist_leninist`: signal=too_close_to_call; q-net=0.0; raw-net=8.0; q-band=±7.1; supports=35; partial+=18; partial-=20; refutes=26; neutral=164; untested=15.
