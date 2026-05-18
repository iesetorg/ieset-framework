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
| `chicago_monetarism` | positive_lean | 23.1 | ±5.0 | 39.5 | 24 | 135 | 40 | 32 | 1 | 16 | 46 | 10 |
| `ordoliberal` | positive_lean | 20.1 | ±5.0 | 34.5 | 22 | 152 | 44 | 25 | 0 | 22 | 61 | 10 |
| `classical_liberal` | positive_lean | 20.1 | ±5.2 | 32.0 | 20 | 179 | 54 | 25 | 1 | 34 | 65 | 12 |
| `austrian` | positive_lean | 17.4 | ±5.0 | 30.5 | 17 | 134 | 36 | 27 | 0 | 19 | 52 | 8 |
| `developmentalism` | positive_lean | 14.0 | ±5.0 | 46.5 | 43 | 143 | 53 | 8 | 1 | 10 | 71 | 8 |
| `new_keynesian` | positive_lean | 4.2 | ±5.0 | 12.5 | 5 | 128 | 15 | 15 | 0 | 10 | 88 | 9 |
| `institutionalism` | positive_lean | 3.6 | ±5.0 | 10.0 | 5 | 131 | 14 | 11 | 1 | 9 | 96 | 11 |
| `marxian` | negative_lean | -1.8 | ±5.0 | 2.0 | 2 | 128 | 26 | 18 | 18 | 24 | 42 | 12 |
| `post_keynesian` | negative_lean | -1.9 | ±5.0 | 4.0 | 7 | 127 | 29 | 13 | 19 | 22 | 44 | 10 |
| `marxist_leninist` | negative_lean | -3.0 | ±5.0 | 2.0 | 3 | 121 | 21 | 18 | 20 | 18 | 44 | 14 |
| `mmt` | negative_lean | -3.0 | ±5.0 | 1.5 | 5 | 125 | 26 | 11 | 18 | 21 | 49 | 11 |
| `social_democratic` | negative_lean | -3.2 | ±5.0 | 1.5 | 2 | 145 | 30 | 18 | 19 | 28 | 50 | 8 |
| `market_socialist` | negative_lean | -3.5 | ±5.0 | 1.5 | 2 | 126 | 24 | 17 | 18 | 22 | 45 | 13 |
| `democratic_socialist` | negative_lean | -4.0 | ±5.0 | 1.0 | 1 | 126 | 23 | 19 | 19 | 22 | 43 | 13 |
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
- `democratic_socialist`: signal=too_close_to_call; lean=negative_lean; q-net=-4.0; raw-net=1.0; q-band=±5.0; supports=23; partial+=19; partial-=19; refutes=22; neutral=43; untested=13.
- `market_socialist`: signal=too_close_to_call; lean=negative_lean; q-net=-3.5; raw-net=1.5; q-band=±5.0; supports=24; partial+=17; partial-=18; refutes=22; neutral=45; untested=13.
- `marxian`: signal=too_close_to_call; lean=negative_lean; q-net=-1.8; raw-net=2.0; q-band=±5.0; supports=26; partial+=18; partial-=18; refutes=24; neutral=42; untested=12.
- `marxist_leninist`: signal=too_close_to_call; lean=negative_lean; q-net=-3.0; raw-net=2.0; q-band=±5.0; supports=21; partial+=18; partial-=20; refutes=18; neutral=44; untested=14.
- `mmt`: signal=too_close_to_call; lean=negative_lean; q-net=-3.0; raw-net=1.5; q-band=±5.0; supports=26; partial+=11; partial-=18; refutes=21; neutral=49; untested=11.
- `post_keynesian`: signal=too_close_to_call; lean=negative_lean; q-net=-1.9; raw-net=4.0; q-band=±5.0; supports=29; partial+=13; partial-=19; refutes=22; neutral=44; untested=10.
- `social_democratic`: signal=too_close_to_call; lean=negative_lean; q-net=-3.2; raw-net=1.5; q-band=±5.0; supports=30; partial+=18; partial-=19; refutes=28; neutral=50; untested=8.

## Marxist-Cluster Readout

- `marxian`: signal=too_close_to_call; q-net=-1.8; raw-net=2.0; q-band=±5.0; supports=26; partial+=18; partial-=18; refutes=24; neutral=42; untested=12.
- `marxist_leninist`: signal=too_close_to_call; q-net=-3.0; raw-net=2.0; q-band=±5.0; supports=21; partial+=18; partial-=20; refutes=18; neutral=44; untested=14.
