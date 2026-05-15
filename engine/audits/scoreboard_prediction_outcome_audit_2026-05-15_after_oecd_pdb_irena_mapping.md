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
| `post_keynesian` | too_close_to_call | negative_lean | -0.2 | ±5.0 | 6.5 | 9 | 124 | 28 | 12 | 17 | 19 | 48 | 12 |
| `marxian` | too_close_to_call | negative_lean | -1.4 | ±5.0 | 3.0 | 3 | 126 | 25 | 16 | 16 | 22 | 47 | 13 |
| `marxist_leninist` | too_close_to_call | negative_lean | -1.6 | ±5.0 | 4.0 | 5 | 120 | 21 | 16 | 18 | 16 | 49 | 15 |
| `mmt` | too_close_to_call | negative_lean | -2.1 | ±5.0 | 3.5 | 6 | 125 | 26 | 11 | 16 | 20 | 52 | 11 |
| `social_democratic` | too_close_to_call | negative_lean | -2.4 | ±5.0 | 2.5 | 3 | 137 | 28 | 16 | 17 | 25 | 51 | 13 |
| `market_socialist` | too_close_to_call | negative_lean | -2.9 | ±5.0 | 3.5 | 4 | 124 | 24 | 15 | 16 | 20 | 49 | 15 |
| `democratic_socialist` | too_close_to_call | negative_lean | -3.4 | ±5.0 | 1.5 | 2 | 122 | 22 | 16 | 17 | 20 | 47 | 17 |
| `eco_socialist` | too_close_to_call | negative_lean | -4.1 | ±5.0 | 1.5 | 2 | 128 | 26 | 15 | 16 | 24 | 47 | 16 |
| `degrowth` | negative_signal | negative_lean | -7.2 | ±5.0 | -8.5 | -7 | 125 | 13 | 13 | 16 | 20 | 63 | 13 |

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

- `degrowth`: signal=negative_signal; lean=negative_lean; q-net=-7.2; raw-net=-8.5; q-band=±5.0; supports=13; partial+=13; partial-=16; refutes=20; neutral=63; untested=13.
- `eco_socialist`: signal=too_close_to_call; lean=negative_lean; q-net=-4.1; raw-net=1.5; q-band=±5.0; supports=26; partial+=15; partial-=16; refutes=24; neutral=47; untested=16.
- `democratic_socialist`: signal=too_close_to_call; lean=negative_lean; q-net=-3.4; raw-net=1.5; q-band=±5.0; supports=22; partial+=16; partial-=17; refutes=20; neutral=47; untested=17.
- `market_socialist`: signal=too_close_to_call; lean=negative_lean; q-net=-2.9; raw-net=3.5; q-band=±5.0; supports=24; partial+=15; partial-=16; refutes=20; neutral=49; untested=15.
- `marxian`: signal=too_close_to_call; lean=negative_lean; q-net=-1.4; raw-net=3.0; q-band=±5.0; supports=25; partial+=16; partial-=16; refutes=22; neutral=47; untested=13.
- `marxist_leninist`: signal=too_close_to_call; lean=negative_lean; q-net=-1.6; raw-net=4.0; q-band=±5.0; supports=21; partial+=16; partial-=18; refutes=16; neutral=49; untested=15.
- `mmt`: signal=too_close_to_call; lean=negative_lean; q-net=-2.1; raw-net=3.5; q-band=±5.0; supports=26; partial+=11; partial-=16; refutes=20; neutral=52; untested=11.
- `post_keynesian`: signal=too_close_to_call; lean=negative_lean; q-net=-0.2; raw-net=6.5; q-band=±5.0; supports=28; partial+=12; partial-=17; refutes=19; neutral=48; untested=12.
- `social_democratic`: signal=too_close_to_call; lean=negative_lean; q-net=-2.4; raw-net=2.5; q-band=±5.0; supports=28; partial+=16; partial-=17; refutes=25; neutral=51; untested=13.

## Marxist-Cluster Readout

- `marxian`: signal=too_close_to_call; q-net=-1.4; raw-net=3.0; q-band=±5.0; supports=25; partial+=16; partial-=16; refutes=22; neutral=47; untested=13.
- `marxist_leninist`: signal=too_close_to_call; q-net=-1.6; raw-net=4.0; q-band=±5.0; supports=21; partial+=16; partial-=18; refutes=16; neutral=49; untested=15.
