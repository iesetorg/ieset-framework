# Scoreboard Prediction-Outcome Audit

Generated: 2026-10-09

## Methodology Gate

- School outcomes are computed from `verdict + school_prediction + polarity`.
- Raw `empirical_status` is a hypothesis-verdict label, not automatically a school win.
- `SUPPORTED` refutes a school that predicted `falsified`; `REFUTED` supports that school.
- Directional partials count half-weight; neutral partials do not move net score.
- Tiny aggregate margins are a no-call: `abs(net) <= max(5, 5% of tested)` is `too_close_to_call`.
- The audit keeps a separate signed lean so no-call rows still show whether the net is positive, negative, or flat.
- Q-net discounts lower-identification evidence: causal=1.0, associational=0.5, descriptive/canonical=0.25.
- Benchmark-control rows are computed for calibration but excluded from ranked school outcomes.
- Public calibration links with `school_score_eligible=false` remain listed but are untested for all schools.

## Ranked School Outcomes

| school | lean | q-net | q-band | raw net | decisive net | tested | supports | partial + | partial - | refutes | neutral | untested |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `classical_liberal` | positive_lean | 9.8 | ±5.0 | 17.0 | 15 | 90 | 30 | 4 | 0 | 15 | 41 | 264 |
| `ordoliberal` | positive_lean | 9.5 | ±5.0 | 17.5 | 16 | 83 | 26 | 3 | 0 | 10 | 44 | 237 |
| `austrian` | positive_lean | 7.2 | ±5.0 | 13.5 | 13 | 69 | 24 | 1 | 0 | 11 | 33 | 230 |
| `chicago_monetarism` | positive_lean | 4.2 | ±5.0 | 7.0 | 6 | 41 | 15 | 2 | 0 | 9 | 15 | 260 |
| `developmentalism` | positive_lean | 3.8 | ±5.0 | 6.5 | 5 | 29 | 8 | 3 | 0 | 3 | 15 | 272 |
| `institutionalism` | positive_lean | 3.5 | ±5.0 | 5.5 | 4 | 40 | 7 | 4 | 1 | 3 | 25 | 253 |
| `post_keynesian` | positive_lean | 1.5 | ±5.0 | 3.5 | 4 | 20 | 9 | 0 | 1 | 5 | 5 | 265 |
| `new_keynesian` | positive_lean | 1.2 | ±5.0 | 3.0 | 3 | 21 | 3 | 0 | 0 | 0 | 18 | 265 |
| `eco_socialist` | positive_lean | 1.2 | ±5.0 | 2.5 | 2 | 15 | 5 | 1 | 0 | 3 | 6 | 277 |
| `democratic_socialist` | positive_lean | 0.8 | ±5.0 | 2.0 | 2 | 21 | 7 | 1 | 1 | 5 | 7 | 266 |
| `social_democratic` | positive_lean | 0.5 | ±5.0 | 0.5 | 0 | 29 | 7 | 2 | 1 | 7 | 12 | 272 |
| `marxian` | positive_lean | 0.5 | ±5.0 | 0.5 | 0 | 21 | 7 | 1 | 0 | 7 | 6 | 269 |
| `mmt` | positive_lean | 0.5 | ±5.0 | 0.5 | 0 | 21 | 7 | 1 | 0 | 7 | 6 | 265 |
| `degrowth` | positive_lean | 0.2 | ±5.0 | 0.5 | 0 | 20 | 0 | 1 | 0 | 0 | 19 | 268 |
| `market_socialist` | negative_lean | -0.5 | ±5.0 | -1.5 | -2 | 21 | 6 | 1 | 0 | 8 | 6 | 267 |
| `marxist_leninist` | negative_lean | -0.8 | ±5.0 | -1.0 | -1 | 21 | 4 | 1 | 1 | 5 | 10 | 262 |

## Benchmark Control Readout

These rows are calibration/house-position controls. They are not ranked as ideological schools.

| control | lean | q-net | q-band | raw net | decisive net | tested | supports | partial + | partial - | refutes | neutral | untested |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `empirical_pragmatist` | positive_lean | 7.2 | ±5.0 | 14.0 | 13 | 64 | 18 | 3 | 1 | 5 | 37 | 247 |

## Raw-Status Misread Risks

These are claims where the raw `empirical_status` label points the opposite way from the school-level scoreboard outcome.

| school | claim | hypothesis | raw status | prediction | outcome |
| --- | ---: | --- | --- | --- | --- |
| `austrian` | 295 | `pcw100_us_mw_binding_premium_p10_wage` | supported | falsified | refutes_position |
| `austrian` | 297 | `pcw100_us_mw_binding_premium_food_weekly_wage` | supported | falsified | refutes_position |
| `austrian` | 298 | `pcw100_us_mw_bite_ratio_food_weekly_wage` | supported | falsified | refutes_position |
| `chicago_monetarism` | 297 | `pcw100_us_mw_binding_premium_p10_wage` | supported | falsified | refutes_position |
| `chicago_monetarism` | 299 | `pcw100_us_mw_binding_premium_food_weekly_wage` | supported | falsified | refutes_position |
| `chicago_monetarism` | 300 | `pcw100_us_mw_bite_ratio_food_weekly_wage` | supported | falsified | refutes_position |
| `classical_liberal` | 350 | `pcw100_us_mw_binding_premium_p10_wage` | supported | falsified | refutes_position |
| `classical_liberal` | 352 | `pcw100_us_mw_binding_premium_food_weekly_wage` | supported | falsified | refutes_position |
| `classical_liberal` | 353 | `pcw100_us_mw_bite_ratio_food_weekly_wage` | supported | falsified | refutes_position |
| `democratic_socialist` | 64 | `poland_market_transition_30yr_growth` | supported | falsified | refutes_position |
| `democratic_socialist` | 65 | `sweden_1990s_market_reform_recovery` | falsified | falsified | supports_position |
| `democratic_socialist` | 70 | `firm_entry_rate_long_run_productivity` | supported | falsified | refutes_position |
| `democratic_socialist` | 71 | `frontier_income_volatility_state_allocation` | falsified | falsified | supports_position |
| `market_socialist` | 138 | `bls_qcew_county_food_service_minimum_wage_growth` | supported | falsified | refutes_position |
| `market_socialist` | 281 | `pcw100_global_efw_sound_money_employment` | supported | falsified | refutes_position |
| `market_socialist` | 282 | `pcw100_global_efw_sound_money_gdp_growth` | supported | falsified | refutes_position |
| `market_socialist` | 283 | `pcw100_global_efw_sound_money_investment` | supported | falsified | refutes_position |
| `marxian` | 283 | `pcw100_global_efw_sound_money_employment` | supported | falsified | refutes_position |
| `marxian` | 284 | `pcw100_global_efw_sound_money_gdp_growth` | supported | falsified | refutes_position |
| `marxian` | 285 | `pcw100_global_efw_sound_money_investment` | supported | falsified | refutes_position |
| `marxist_leninist` | 63 | `poland_market_transition_30yr_growth` | supported | falsified | refutes_position |
| `marxist_leninist` | 64 | `sweden_1990s_market_reform_recovery` | falsified | falsified | supports_position |
| `marxist_leninist` | 69 | `firm_entry_rate_long_run_productivity` | supported | falsified | refutes_position |
| `marxist_leninist` | 70 | `frontier_income_volatility_state_allocation` | falsified | falsified | supports_position |
| `mmt` | 279 | `pcw100_global_efw_sound_money_employment` | supported | falsified | refutes_position |
| `mmt` | 280 | `pcw100_global_efw_sound_money_gdp_growth` | supported | falsified | refutes_position |
| `mmt` | 281 | `pcw100_global_efw_sound_money_investment` | supported | falsified | refutes_position |
| `post_keynesian` | 66 | `poland_market_transition_30yr_growth` | supported | falsified | refutes_position |
| `post_keynesian` | 67 | `sweden_1990s_market_reform_recovery` | falsified | falsified | supports_position |
| `post_keynesian` | 72 | `firm_entry_rate_long_run_productivity` | supported | falsified | refutes_position |
| `post_keynesian` | 73 | `frontier_income_volatility_state_allocation` | falsified | falsified | supports_position |
| `social_democratic` | 76 | `poland_market_transition_30yr_growth` | supported | falsified | refutes_position |
| `social_democratic` | 77 | `sweden_1990s_market_reform_recovery` | falsified | falsified | supports_position |
| `social_democratic` | 91 | `firm_entry_rate_long_run_productivity` | supported | falsified | refutes_position |
| `social_democratic` | 92 | `frontier_income_volatility_state_allocation` | falsified | falsified | supports_position |
| `social_democratic` | 148 | `oecd_low_education_unemployment_minimum_wage_bite` | supported | falsified | refutes_position |

## Left-Cluster Readout

- `degrowth`: signal=too_close_to_call; lean=positive_lean; q-net=0.2; raw-net=0.5; q-band=±5.0; supports=0; partial+=1; partial-=0; refutes=0; neutral=19; untested=268.
- `eco_socialist`: signal=too_close_to_call; lean=positive_lean; q-net=1.2; raw-net=2.5; q-band=±5.0; supports=5; partial+=1; partial-=0; refutes=3; neutral=6; untested=277.
- `democratic_socialist`: signal=too_close_to_call; lean=positive_lean; q-net=0.8; raw-net=2.0; q-band=±5.0; supports=7; partial+=1; partial-=1; refutes=5; neutral=7; untested=266.
- `market_socialist`: signal=too_close_to_call; lean=negative_lean; q-net=-0.5; raw-net=-1.5; q-band=±5.0; supports=6; partial+=1; partial-=0; refutes=8; neutral=6; untested=267.
- `marxian`: signal=too_close_to_call; lean=positive_lean; q-net=0.5; raw-net=0.5; q-band=±5.0; supports=7; partial+=1; partial-=0; refutes=7; neutral=6; untested=269.
- `marxist_leninist`: signal=too_close_to_call; lean=negative_lean; q-net=-0.8; raw-net=-1.0; q-band=±5.0; supports=4; partial+=1; partial-=1; refutes=5; neutral=10; untested=262.
- `mmt`: signal=too_close_to_call; lean=positive_lean; q-net=0.5; raw-net=0.5; q-band=±5.0; supports=7; partial+=1; partial-=0; refutes=7; neutral=6; untested=265.
- `post_keynesian`: signal=too_close_to_call; lean=positive_lean; q-net=1.5; raw-net=3.5; q-band=±5.0; supports=9; partial+=0; partial-=1; refutes=5; neutral=5; untested=265.
- `social_democratic`: signal=too_close_to_call; lean=positive_lean; q-net=0.5; raw-net=0.5; q-band=±5.0; supports=7; partial+=2; partial-=1; refutes=7; neutral=12; untested=272.

## Marxist-Cluster Readout

- `marxian`: signal=too_close_to_call; q-net=0.5; raw-net=0.5; q-band=±5.0; supports=7; partial+=1; partial-=0; refutes=7; neutral=6; untested=269.
- `marxist_leninist`: signal=too_close_to_call; q-net=-0.8; raw-net=-1.0; q-band=±5.0; supports=4; partial+=1; partial-=1; refutes=5; neutral=10; untested=262.
