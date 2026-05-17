# Scoreboard Prediction-Outcome Audit

Generated: 2026-05-17

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
| `chicago_monetarism` | positive_lean | 21.6 | ±5.0 | 37.0 | 22 | 134 | 39 | 31 | 1 | 17 | 46 | 11 |
| `ordoliberal` | positive_lean | 19.6 | ±5.0 | 34.0 | 22 | 152 | 44 | 24 | 0 | 22 | 62 | 10 |
| `classical_liberal` | positive_lean | 19.1 | ±5.2 | 30.5 | 19 | 179 | 54 | 24 | 1 | 35 | 65 | 12 |
| `austrian` | positive_lean | 16.4 | ±5.0 | 29.0 | 16 | 134 | 36 | 26 | 0 | 20 | 52 | 8 |
| `developmentalism` | positive_lean | 14.5 | ±5.0 | 47.5 | 44 | 143 | 54 | 8 | 1 | 10 | 70 | 8 |
| `new_keynesian` | positive_lean | 4.5 | ±5.0 | 13.0 | 6 | 127 | 16 | 14 | 0 | 10 | 87 | 10 |
| `institutionalism` | positive_lean | 4.1 | ±5.0 | 11.0 | 6 | 130 | 15 | 11 | 1 | 9 | 94 | 12 |
| `post_keynesian` | negative_lean | -0.9 | ±5.0 | 5.5 | 8 | 125 | 29 | 13 | 18 | 21 | 44 | 12 |
| `marxian` | negative_lean | -1.0 | ±5.0 | 3.0 | 3 | 127 | 26 | 17 | 17 | 23 | 44 | 13 |
| `mmt` | negative_lean | -2.5 | ±5.0 | 2.0 | 5 | 125 | 26 | 11 | 17 | 21 | 50 | 11 |
| `marxist_leninist` | negative_lean | -2.8 | ±5.0 | 2.0 | 3 | 120 | 21 | 17 | 19 | 18 | 45 | 15 |
| `social_democratic` | negative_lean | -3.0 | ±5.0 | 1.5 | 2 | 140 | 30 | 17 | 18 | 28 | 47 | 13 |
| `market_socialist` | negative_lean | -3.2 | ±5.0 | 1.5 | 2 | 125 | 24 | 16 | 17 | 22 | 46 | 14 |
| `eco_socialist` | negative_lean | -4.2 | ±5.0 | 0.5 | 1 | 130 | 27 | 16 | 17 | 26 | 44 | 15 |
| `democratic_socialist` | negative_lean | -4.5 | ±5.0 | -0.5 | 0 | 122 | 22 | 17 | 18 | 22 | 43 | 17 |
| `degrowth` | negative_lean | -7.1 | ±5.0 | -8.5 | -7 | 126 | 14 | 14 | 17 | 21 | 60 | 13 |

## Benchmark Control Readout

These rows are calibration/house-position controls. They are not ranked as ideological schools.

| control | lean | q-net | q-band | raw net | decisive net | tested | supports | partial + | partial - | refutes | neutral | untested |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `empirical_pragmatist` | positive_lean | 12.0 | ±5.0 | 23.5 | 20 | 150 | 31 | 8 | 1 | 11 | 99 | 8 |

## Raw-Status Misread Risks

These are claims where the raw `empirical_status` label points the opposite way from the school-level scoreboard outcome.

| school | claim | hypothesis | raw status | prediction | outcome |
| --- | ---: | --- | --- | --- | --- |
| `austrian` | 68 | `industrial_policy_high_governance_success` | supported | falsified | refutes_position |
| `chicago_monetarism` | 69 | `industrial_policy_high_governance_success` | supported | falsified | refutes_position |
| `classical_liberal` | 78 | `industrial_policy_high_governance_success` | supported | falsified | refutes_position |
| `democratic_socialist` | 64 | `poland_market_transition_30yr_growth` | supported | falsified | refutes_position |
| `democratic_socialist` | 65 | `sweden_1990s_market_reform_recovery` | falsified | falsified | supports_position |
| `democratic_socialist` | 70 | `firm_entry_rate_long_run_productivity` | supported | falsified | refutes_position |
| `democratic_socialist` | 71 | `frontier_income_volatility_state_allocation` | falsified | falsified | supports_position |
| `developmentalism` | 130 | `bank_state_ownership_credit_misallocation` | falsified | falsified | supports_position |
| `developmentalism` | 131 | `venture_capital_market_depth_innovation` | falsified | falsified | supports_position |
| `market_socialist` | 138 | `bls_qcew_county_food_service_minimum_wage_growth` | supported | falsified | refutes_position |
| `marxist_leninist` | 63 | `poland_market_transition_30yr_growth` | supported | falsified | refutes_position |
| `marxist_leninist` | 64 | `sweden_1990s_market_reform_recovery` | falsified | falsified | supports_position |
| `marxist_leninist` | 69 | `firm_entry_rate_long_run_productivity` | supported | falsified | refutes_position |
| `marxist_leninist` | 70 | `frontier_income_volatility_state_allocation` | falsified | falsified | supports_position |
| `post_keynesian` | 66 | `poland_market_transition_30yr_growth` | supported | falsified | refutes_position |
| `post_keynesian` | 67 | `sweden_1990s_market_reform_recovery` | falsified | falsified | supports_position |
| `post_keynesian` | 72 | `firm_entry_rate_long_run_productivity` | supported | falsified | refutes_position |
| `post_keynesian` | 73 | `frontier_income_volatility_state_allocation` | falsified | falsified | supports_position |
| `social_democratic` | 69 | `oecd_collective_bargaining_growth_penalty_kei` | falsified | supported | supports_position |
| `social_democratic` | 76 | `poland_market_transition_30yr_growth` | supported | falsified | refutes_position |
| `social_democratic` | 77 | `sweden_1990s_market_reform_recovery` | falsified | falsified | supports_position |
| `social_democratic` | 91 | `firm_entry_rate_long_run_productivity` | supported | falsified | refutes_position |
| `social_democratic` | 92 | `frontier_income_volatility_state_allocation` | falsified | falsified | supports_position |
| `social_democratic` | 148 | `oecd_low_education_unemployment_minimum_wage_bite` | supported | falsified | refutes_position |

## Left-Cluster Readout

- `degrowth`: signal=negative_signal; lean=negative_lean; q-net=-7.1; raw-net=-8.5; q-band=±5.0; supports=14; partial+=14; partial-=17; refutes=21; neutral=60; untested=13.
- `eco_socialist`: signal=too_close_to_call; lean=negative_lean; q-net=-4.2; raw-net=0.5; q-band=±5.0; supports=27; partial+=16; partial-=17; refutes=26; neutral=44; untested=15.
- `democratic_socialist`: signal=too_close_to_call; lean=negative_lean; q-net=-4.5; raw-net=-0.5; q-band=±5.0; supports=22; partial+=17; partial-=18; refutes=22; neutral=43; untested=17.
- `market_socialist`: signal=too_close_to_call; lean=negative_lean; q-net=-3.2; raw-net=1.5; q-band=±5.0; supports=24; partial+=16; partial-=17; refutes=22; neutral=46; untested=14.
- `marxian`: signal=too_close_to_call; lean=negative_lean; q-net=-1.0; raw-net=3.0; q-band=±5.0; supports=26; partial+=17; partial-=17; refutes=23; neutral=44; untested=13.
- `marxist_leninist`: signal=too_close_to_call; lean=negative_lean; q-net=-2.8; raw-net=2.0; q-band=±5.0; supports=21; partial+=17; partial-=19; refutes=18; neutral=45; untested=15.
- `mmt`: signal=too_close_to_call; lean=negative_lean; q-net=-2.5; raw-net=2.0; q-band=±5.0; supports=26; partial+=11; partial-=17; refutes=21; neutral=50; untested=11.
- `post_keynesian`: signal=too_close_to_call; lean=negative_lean; q-net=-0.9; raw-net=5.5; q-band=±5.0; supports=29; partial+=13; partial-=18; refutes=21; neutral=44; untested=12.
- `social_democratic`: signal=too_close_to_call; lean=negative_lean; q-net=-3.0; raw-net=1.5; q-band=±5.0; supports=30; partial+=17; partial-=18; refutes=28; neutral=47; untested=13.

## Marxist-Cluster Readout

- `marxian`: signal=too_close_to_call; q-net=-1.0; raw-net=3.0; q-band=±5.0; supports=26; partial+=17; partial-=17; refutes=23; neutral=44; untested=13.
- `marxist_leninist`: signal=too_close_to_call; q-net=-2.8; raw-net=2.0; q-band=±5.0; supports=21; partial+=17; partial-=19; refutes=18; neutral=45; untested=15.
