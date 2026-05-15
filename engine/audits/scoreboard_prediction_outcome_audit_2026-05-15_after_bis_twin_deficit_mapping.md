# Scoreboard Prediction-Outcome Audit

Generated: 2026-05-15

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
| `chicago_monetarism` | positive_signal | positive_lean | 22.0 | ±5.0 | 37.5 | 23 | 129 | 36 | 30 | 1 | 13 | 49 | 10 |
| `ordoliberal` | positive_signal | positive_lean | 18.2 | ±5.0 | 31.5 | 20 | 151 | 42 | 23 | 0 | 22 | 64 | 10 |
| `austrian` | positive_signal | positive_lean | 17.2 | ±5.0 | 28.5 | 16 | 134 | 35 | 25 | 0 | 19 | 55 | 7 |
| `classical_liberal` | positive_signal | positive_lean | 17.2 | ±5.1 | 27.5 | 17 | 170 | 48 | 22 | 1 | 31 | 68 | 12 |
| `developmentalism` | positive_signal | positive_lean | 13.0 | ±5.0 | 44.5 | 41 | 136 | 49 | 7 | 0 | 8 | 72 | 9 |
| `empirical_pragmatist` | positive_signal | positive_lean | 9.2 | ±5.0 | 17.5 | 15 | 141 | 25 | 6 | 1 | 10 | 99 | 9 |
| `new_keynesian` | too_close_to_call | positive_lean | 4.0 | ±5.0 | 12.0 | 5 | 126 | 15 | 14 | 0 | 10 | 87 | 11 |
| `institutionalism` | too_close_to_call | positive_lean | 3.6 | ±5.0 | 10.0 | 5 | 129 | 13 | 11 | 1 | 8 | 96 | 12 |
| `post_keynesian` | too_close_to_call | positive_lean | 0.5 | ±5.0 | 8.0 | 10 | 125 | 29 | 13 | 17 | 19 | 47 | 12 |
| `marxian` | too_close_to_call | negative_lean | -0.6 | ±5.0 | 4.5 | 4 | 127 | 26 | 17 | 16 | 22 | 46 | 13 |
| `marxist_leninist` | too_close_to_call | negative_lean | -1.4 | ±5.0 | 4.5 | 5 | 120 | 21 | 17 | 18 | 16 | 48 | 15 |
| `mmt` | too_close_to_call | negative_lean | -1.9 | ±5.0 | 4.0 | 6 | 125 | 26 | 12 | 16 | 20 | 51 | 11 |
| `social_democratic` | too_close_to_call | negative_lean | -2.1 | ±5.0 | 3.0 | 3 | 137 | 28 | 17 | 17 | 25 | 50 | 13 |
| `market_socialist` | too_close_to_call | negative_lean | -2.6 | ±5.0 | 4.0 | 4 | 124 | 24 | 16 | 16 | 20 | 48 | 15 |
| `democratic_socialist` | too_close_to_call | negative_lean | -3.1 | ±5.0 | 2.0 | 2 | 122 | 22 | 17 | 17 | 20 | 46 | 17 |
| `eco_socialist` | too_close_to_call | negative_lean | -3.9 | ±5.0 | 2.0 | 2 | 128 | 26 | 16 | 16 | 24 | 46 | 16 |
| `degrowth` | negative_signal | negative_lean | -7.0 | ±5.0 | -8.0 | -7 | 125 | 13 | 14 | 16 | 20 | 62 | 13 |

## Raw-Status Misread Risks

These are claims where the raw `empirical_status` label points the opposite way from the school-level scoreboard outcome.

| school | claim | hypothesis | raw status | prediction | outcome |
| --- | ---: | --- | --- | --- | --- |
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

- `degrowth`: signal=negative_signal; lean=negative_lean; q-net=-7.0; raw-net=-8.0; q-band=±5.0; supports=13; partial+=14; partial-=16; refutes=20; neutral=62; untested=13.
- `eco_socialist`: signal=too_close_to_call; lean=negative_lean; q-net=-3.9; raw-net=2.0; q-band=±5.0; supports=26; partial+=16; partial-=16; refutes=24; neutral=46; untested=16.
- `democratic_socialist`: signal=too_close_to_call; lean=negative_lean; q-net=-3.1; raw-net=2.0; q-band=±5.0; supports=22; partial+=17; partial-=17; refutes=20; neutral=46; untested=17.
- `market_socialist`: signal=too_close_to_call; lean=negative_lean; q-net=-2.6; raw-net=4.0; q-band=±5.0; supports=24; partial+=16; partial-=16; refutes=20; neutral=48; untested=15.
- `marxian`: signal=too_close_to_call; lean=negative_lean; q-net=-0.6; raw-net=4.5; q-band=±5.0; supports=26; partial+=17; partial-=16; refutes=22; neutral=46; untested=13.
- `marxist_leninist`: signal=too_close_to_call; lean=negative_lean; q-net=-1.4; raw-net=4.5; q-band=±5.0; supports=21; partial+=17; partial-=18; refutes=16; neutral=48; untested=15.
- `mmt`: signal=too_close_to_call; lean=negative_lean; q-net=-1.9; raw-net=4.0; q-band=±5.0; supports=26; partial+=12; partial-=16; refutes=20; neutral=51; untested=11.
- `post_keynesian`: signal=too_close_to_call; lean=positive_lean; q-net=0.5; raw-net=8.0; q-band=±5.0; supports=29; partial+=13; partial-=17; refutes=19; neutral=47; untested=12.
- `social_democratic`: signal=too_close_to_call; lean=negative_lean; q-net=-2.1; raw-net=3.0; q-band=±5.0; supports=28; partial+=17; partial-=17; refutes=25; neutral=50; untested=13.

## Marxist-Cluster Readout

- `marxian`: signal=too_close_to_call; q-net=-0.6; raw-net=4.5; q-band=±5.0; supports=26; partial+=17; partial-=16; refutes=22; neutral=46; untested=13.
- `marxist_leninist`: signal=too_close_to_call; q-net=-1.4; raw-net=4.5; q-band=±5.0; supports=21; partial+=17; partial-=18; refutes=16; neutral=48; untested=15.
