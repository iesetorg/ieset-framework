# Scoreboard Prediction-Outcome Audit

Generated: 2026-05-13

## Methodology Gate

- School outcomes are computed from `verdict + school_prediction + polarity`.
- Raw `empirical_status` is a hypothesis-verdict label, not automatically a school win.
- `SUPPORTED` refutes a school that predicted `falsified`; `REFUTED` supports that school.
- Directional partials count half-weight; neutral partials do not move net score.
- Tiny aggregate margins are a no-call: `abs(net) <= max(5, 5% of tested)` is `too_close_to_call`.
- The audit keeps a separate signed lean so no-call rows still show whether the net is positive, negative, or flat.
- Q-net discounts lower-identification evidence: causal=1.0, associational=0.5, descriptive/canonical=0.25.

## Ranked School Outcomes

| school | signal | lean | q-net | q-band | raw net | decisive net | tested | supports | partial + | partial - | refutes | neutral | untested |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `chicago_monetarism` | positive_signal | positive_lean | 22.0 | ±5.0 | 37.5 | 23 | 129 | 36 | 30 | 1 | 13 | 49 | 8 |
| `ordoliberal` | positive_signal | positive_lean | 20.2 | ±5.0 | 33.5 | 22 | 151 | 43 | 23 | 0 | 21 | 64 | 8 |
| `austrian` | positive_signal | positive_lean | 17.2 | ±5.0 | 28.5 | 16 | 134 | 35 | 25 | 0 | 19 | 55 | 6 |
| `classical_liberal` | positive_signal | positive_lean | 17.2 | ±5.1 | 27.5 | 17 | 170 | 48 | 22 | 1 | 31 | 68 | 9 |
| `developmentalism` | positive_signal | positive_lean | 13.0 | ±5.0 | 44.5 | 41 | 136 | 49 | 7 | 0 | 8 | 72 | 9 |
| `empirical_pragmatist` | positive_signal | positive_lean | 9.2 | ±5.0 | 17.5 | 15 | 141 | 25 | 6 | 1 | 10 | 99 | 8 |
| `new_keynesian` | too_close_to_call | positive_lean | 4.0 | ±5.0 | 12.0 | 5 | 126 | 15 | 14 | 0 | 10 | 87 | 11 |
| `institutionalism` | too_close_to_call | positive_lean | 3.6 | ±5.0 | 10.0 | 5 | 129 | 13 | 11 | 1 | 8 | 96 | 11 |
| `post_keynesian` | too_close_to_call | negative_lean | -2.2 | ±5.0 | 4.5 | 7 | 124 | 27 | 12 | 17 | 20 | 48 | 12 |
| `marxian` | too_close_to_call | negative_lean | -3.4 | ±5.0 | 1.0 | 1 | 126 | 24 | 16 | 16 | 23 | 47 | 13 |
| `marxist_leninist` | too_close_to_call | negative_lean | -3.6 | ±5.0 | 2.0 | 3 | 120 | 20 | 16 | 18 | 17 | 49 | 15 |
| `mmt` | too_close_to_call | negative_lean | -4.1 | ±5.0 | 1.5 | 4 | 125 | 25 | 11 | 16 | 21 | 52 | 11 |
| `social_democratic` | too_close_to_call | negative_lean | -4.4 | ±5.0 | 0.5 | 1 | 137 | 27 | 16 | 17 | 26 | 51 | 12 |
| `market_socialist` | too_close_to_call | negative_lean | -4.9 | ±5.0 | 1.5 | 2 | 124 | 23 | 15 | 16 | 21 | 49 | 15 |
| `democratic_socialist` | negative_signal | negative_lean | -5.4 | ±5.0 | -0.5 | 0 | 122 | 21 | 16 | 17 | 21 | 47 | 17 |
| `eco_socialist` | negative_signal | negative_lean | -6.1 | ±5.0 | -0.5 | 0 | 128 | 25 | 15 | 16 | 25 | 47 | 16 |
| `degrowth` | negative_signal | negative_lean | -9.2 | ±5.0 | -10.5 | -9 | 125 | 12 | 13 | 16 | 21 | 63 | 13 |

## Raw-Status Misread Risks

These are claims where the raw `empirical_status` label points the opposite way from the school-level scoreboard outcome.

| school | claim | hypothesis | raw status | prediction | outcome |
| --- | ---: | --- | --- | --- | --- |
| `austrian` | 132 | `debt_overhang_private_investment_30yr` | supported | supported | refutes_position |
| `chicago_monetarism` | 131 | `debt_overhang_private_investment_30yr` | supported | supported | refutes_position |
| `classical_liberal` | 159 | `debt_overhang_private_investment_30yr` | supported | supported | refutes_position |
| `democratic_socialist` | 65 | `sweden_1990s_market_reform_recovery` | falsified | falsified | supports_position |
| `democratic_socialist` | 70 | `firm_entry_rate_long_run_productivity` | supported | falsified | refutes_position |
| `democratic_socialist` | 71 | `frontier_income_volatility_state_allocation` | falsified | falsified | supports_position |
| `developmentalism` | 130 | `bank_state_ownership_credit_misallocation` | falsified | falsified | supports_position |
| `developmentalism` | 131 | `venture_capital_market_depth_innovation` | falsified | falsified | supports_position |
| `market_socialist` | 138 | `bls_qcew_county_food_service_minimum_wage_growth` | supported | falsified | refutes_position |
| `marxist_leninist` | 64 | `sweden_1990s_market_reform_recovery` | falsified | falsified | supports_position |
| `marxist_leninist` | 69 | `firm_entry_rate_long_run_productivity` | supported | falsified | refutes_position |
| `marxist_leninist` | 70 | `frontier_income_volatility_state_allocation` | falsified | falsified | supports_position |
| `post_keynesian` | 67 | `sweden_1990s_market_reform_recovery` | falsified | falsified | supports_position |
| `post_keynesian` | 72 | `firm_entry_rate_long_run_productivity` | supported | falsified | refutes_position |
| `post_keynesian` | 73 | `frontier_income_volatility_state_allocation` | falsified | falsified | supports_position |
| `social_democratic` | 69 | `oecd_collective_bargaining_growth_penalty_kei` | falsified | supported | supports_position |
| `social_democratic` | 77 | `sweden_1990s_market_reform_recovery` | falsified | falsified | supports_position |
| `social_democratic` | 91 | `firm_entry_rate_long_run_productivity` | supported | falsified | refutes_position |
| `social_democratic` | 92 | `frontier_income_volatility_state_allocation` | falsified | falsified | supports_position |
| `social_democratic` | 148 | `oecd_low_education_unemployment_minimum_wage_bite` | supported | falsified | refutes_position |

## Left-Cluster Readout

- `degrowth`: signal=negative_signal; lean=negative_lean; q-net=-9.2; raw-net=-10.5; q-band=±5.0; supports=12; partial+=13; partial-=16; refutes=21; neutral=63; untested=13.
- `eco_socialist`: signal=negative_signal; lean=negative_lean; q-net=-6.1; raw-net=-0.5; q-band=±5.0; supports=25; partial+=15; partial-=16; refutes=25; neutral=47; untested=16.
- `democratic_socialist`: signal=negative_signal; lean=negative_lean; q-net=-5.4; raw-net=-0.5; q-band=±5.0; supports=21; partial+=16; partial-=17; refutes=21; neutral=47; untested=17.
- `market_socialist`: signal=too_close_to_call; lean=negative_lean; q-net=-4.9; raw-net=1.5; q-band=±5.0; supports=23; partial+=15; partial-=16; refutes=21; neutral=49; untested=15.
- `marxian`: signal=too_close_to_call; lean=negative_lean; q-net=-3.4; raw-net=1.0; q-band=±5.0; supports=24; partial+=16; partial-=16; refutes=23; neutral=47; untested=13.
- `marxist_leninist`: signal=too_close_to_call; lean=negative_lean; q-net=-3.6; raw-net=2.0; q-band=±5.0; supports=20; partial+=16; partial-=18; refutes=17; neutral=49; untested=15.
- `mmt`: signal=too_close_to_call; lean=negative_lean; q-net=-4.1; raw-net=1.5; q-band=±5.0; supports=25; partial+=11; partial-=16; refutes=21; neutral=52; untested=11.
- `post_keynesian`: signal=too_close_to_call; lean=negative_lean; q-net=-2.2; raw-net=4.5; q-band=±5.0; supports=27; partial+=12; partial-=17; refutes=20; neutral=48; untested=12.
- `social_democratic`: signal=too_close_to_call; lean=negative_lean; q-net=-4.4; raw-net=0.5; q-band=±5.0; supports=27; partial+=16; partial-=17; refutes=26; neutral=51; untested=12.

## Marxist-Cluster Readout

- `marxian`: signal=too_close_to_call; q-net=-3.4; raw-net=1.0; q-band=±5.0; supports=24; partial+=16; partial-=16; refutes=23; neutral=47; untested=13.
- `marxist_leninist`: signal=too_close_to_call; q-net=-3.6; raw-net=2.0; q-band=±5.0; supports=20; partial+=16; partial-=18; refutes=17; neutral=49; untested=15.
