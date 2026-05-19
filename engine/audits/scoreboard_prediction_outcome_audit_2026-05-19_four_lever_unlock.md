# Scoreboard Prediction-Outcome Audit

Generated: 2026-05-19

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
| `chicago_monetarism` | positive_lean | 24.4 | ±5.0 | 43.0 | 27 | 141 | 44 | 33 | 1 | 17 | 46 | 10 |
| `classical_liberal` | positive_lean | 21.6 | ±5.4 | 36.5 | 24 | 186 | 59 | 26 | 1 | 35 | 65 | 12 |
| `ordoliberal` | positive_lean | 20.9 | ±5.0 | 36.5 | 24 | 154 | 46 | 25 | 0 | 22 | 61 | 10 |
| `austrian` | positive_lean | 17.9 | ±5.0 | 31.5 | 18 | 137 | 38 | 27 | 0 | 20 | 52 | 8 |
| `developmentalism` | positive_lean | 15.0 | ±5.0 | 49.5 | 46 | 146 | 56 | 8 | 1 | 10 | 71 | 8 |
| `new_keynesian` | positive_lean | 5.2 | ±5.0 | 14.5 | 7 | 130 | 17 | 15 | 0 | 10 | 88 | 9 |
| `institutionalism` | positive_lean | 4.9 | ±5.0 | 13.0 | 8 | 134 | 17 | 11 | 1 | 9 | 96 | 11 |
| `post_keynesian` | negative_lean | -1.9 | ±5.0 | 4.0 | 7 | 129 | 30 | 13 | 19 | 23 | 44 | 10 |
| `marxian` | negative_lean | -2.2 | ±5.0 | 1.0 | 1 | 129 | 26 | 18 | 18 | 25 | 42 | 12 |
| `marxist_leninist` | negative_lean | -2.5 | ±5.0 | 3.0 | 4 | 122 | 22 | 18 | 20 | 18 | 44 | 14 |
| `social_democratic` | negative_lean | -2.8 | ±5.0 | 2.5 | 3 | 146 | 31 | 18 | 19 | 28 | 50 | 8 |
| `democratic_socialist` | negative_lean | -3.5 | ±5.0 | 2.0 | 2 | 127 | 24 | 19 | 19 | 22 | 43 | 13 |
| `market_socialist` | negative_lean | -3.5 | ±5.0 | 1.5 | 2 | 126 | 24 | 17 | 18 | 22 | 45 | 13 |
| `mmt` | negative_lean | -3.5 | ±5.0 | 0.5 | 4 | 126 | 26 | 11 | 18 | 22 | 49 | 11 |
| `eco_socialist` | negative_lean | -4.5 | ±5.0 | 0.5 | 1 | 131 | 27 | 17 | 18 | 26 | 43 | 14 |
| `degrowth` | negative_lean | -7.6 | ±5.0 | -9.0 | -7 | 127 | 14 | 14 | 18 | 21 | 60 | 12 |

## Benchmark Control Readout

These rows are calibration/house-position controls. They are not ranked as ideological schools.

| control | lean | q-net | q-band | raw net | decisive net | tested | supports | partial + | partial - | refutes | neutral | untested |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `empirical_pragmatist` | positive_lean | 11.8 | ±5.0 | 23.0 | 19 | 151 | 30 | 9 | 1 | 11 | 100 | 7 |

## Raw-Status Misread Risks

These are claims where the raw `empirical_status` label points the opposite way from the school-level scoreboard outcome.

| school | claim | hypothesis | raw status | prediction | outcome |
| --- | ---: | --- | --- | --- | --- |
| `democratic_socialist` | 64 | `poland_market_transition_30yr_growth` | supported | falsified | refutes_position |
| `democratic_socialist` | 65 | `sweden_1990s_market_reform_recovery` | falsified | falsified | supports_position |
| `democratic_socialist` | 70 | `firm_entry_rate_long_run_productivity` | supported | falsified | refutes_position |
| `democratic_socialist` | 71 | `frontier_income_volatility_state_allocation` | falsified | falsified | supports_position |
| `developmentalism` | 130 | `bank_state_ownership_credit_misallocation` | falsified | falsified | supports_position |
| `developmentalism` | 131 | `venture_capital_market_depth_innovation` | falsified | falsified | supports_position |
| `developmentalism` | 152 | `korea_post_chaebol_liberalisation_frontier_growth` | falsified | falsified | supports_position |
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

- `degrowth`: signal=negative_signal; lean=negative_lean; q-net=-7.6; raw-net=-9.0; q-band=±5.0; supports=14; partial+=14; partial-=18; refutes=21; neutral=60; untested=12.
- `eco_socialist`: signal=too_close_to_call; lean=negative_lean; q-net=-4.5; raw-net=0.5; q-band=±5.0; supports=27; partial+=17; partial-=18; refutes=26; neutral=43; untested=14.
- `democratic_socialist`: signal=too_close_to_call; lean=negative_lean; q-net=-3.5; raw-net=2.0; q-band=±5.0; supports=24; partial+=19; partial-=19; refutes=22; neutral=43; untested=13.
- `market_socialist`: signal=too_close_to_call; lean=negative_lean; q-net=-3.5; raw-net=1.5; q-band=±5.0; supports=24; partial+=17; partial-=18; refutes=22; neutral=45; untested=13.
- `marxian`: signal=too_close_to_call; lean=negative_lean; q-net=-2.2; raw-net=1.0; q-band=±5.0; supports=26; partial+=18; partial-=18; refutes=25; neutral=42; untested=12.
- `marxist_leninist`: signal=too_close_to_call; lean=negative_lean; q-net=-2.5; raw-net=3.0; q-band=±5.0; supports=22; partial+=18; partial-=20; refutes=18; neutral=44; untested=14.
- `mmt`: signal=too_close_to_call; lean=negative_lean; q-net=-3.5; raw-net=0.5; q-band=±5.0; supports=26; partial+=11; partial-=18; refutes=22; neutral=49; untested=11.
- `post_keynesian`: signal=too_close_to_call; lean=negative_lean; q-net=-1.9; raw-net=4.0; q-band=±5.0; supports=30; partial+=13; partial-=19; refutes=23; neutral=44; untested=10.
- `social_democratic`: signal=too_close_to_call; lean=negative_lean; q-net=-2.8; raw-net=2.5; q-band=±5.0; supports=31; partial+=18; partial-=19; refutes=28; neutral=50; untested=8.

## Marxist-Cluster Readout

- `marxian`: signal=too_close_to_call; q-net=-2.2; raw-net=1.0; q-band=±5.0; supports=26; partial+=18; partial-=18; refutes=25; neutral=42; untested=12.
- `marxist_leninist`: signal=too_close_to_call; q-net=-2.5; raw-net=3.0; q-band=±5.0; supports=22; partial+=18; partial-=20; refutes=18; neutral=44; untested=14.
