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
| `chicago_monetarism` | positive_signal | positive_lean | 21.8 | ±5.0 | 36.5 | 22 | 126 | 34 | 30 | 1 | 12 | 49 | 8 |
| `ordoliberal` | positive_signal | positive_lean | 19.2 | ±5.0 | 33.5 | 22 | 145 | 40 | 23 | 0 | 18 | 64 | 8 |
| `austrian` | positive_signal | positive_lean | 17.8 | ±5.0 | 29.5 | 17 | 131 | 34 | 25 | 0 | 17 | 55 | 6 |
| `classical_liberal` | positive_signal | positive_lean | 17.8 | ±5.0 | 28.5 | 18 | 159 | 43 | 22 | 1 | 25 | 68 | 9 |
| `developmentalism` | positive_signal | positive_lean | 11.5 | ±5.0 | 42.5 | 40 | 127 | 45 | 5 | 0 | 5 | 72 | 9 |
| `empirical_pragmatist` | positive_signal | positive_lean | 6.0 | ±5.0 | 10.0 | 7 | 126 | 14 | 6 | 0 | 7 | 99 | 8 |
| `institutionalism` | too_close_to_call | positive_lean | 4.1 | ±5.0 | 11.5 | 7 | 124 | 13 | 9 | 0 | 6 | 96 | 11 |
| `new_keynesian` | too_close_to_call | positive_lean | 3.8 | ±5.0 | 11.0 | 4 | 123 | 14 | 14 | 0 | 10 | 85 | 13 |
| `post_keynesian` | too_close_to_call | negative_lean | -0.2 | ±5.0 | 6.5 | 9 | 124 | 28 | 12 | 17 | 19 | 48 | 12 |
| `marxian` | too_close_to_call | negative_lean | -1.4 | ±5.0 | 3.0 | 3 | 125 | 25 | 16 | 16 | 22 | 46 | 14 |
| `marxist_leninist` | too_close_to_call | negative_lean | -1.6 | ±5.0 | 4.0 | 5 | 120 | 21 | 16 | 18 | 16 | 49 | 15 |
| `mmt` | too_close_to_call | negative_lean | -2.1 | ±5.0 | 3.5 | 6 | 124 | 26 | 11 | 16 | 20 | 51 | 12 |
| `market_socialist` | too_close_to_call | negative_lean | -2.4 | ±5.0 | 4.5 | 5 | 122 | 24 | 15 | 16 | 19 | 48 | 16 |
| `democratic_socialist` | too_close_to_call | negative_lean | -3.4 | ±5.0 | 1.5 | 2 | 122 | 22 | 16 | 17 | 20 | 47 | 17 |
| `eco_socialist` | too_close_to_call | negative_lean | -4.1 | ±5.0 | 1.5 | 2 | 128 | 26 | 15 | 16 | 24 | 47 | 16 |
| `social_democratic` | too_close_to_call | negative_lean | -4.4 | ±5.0 | -0.5 | 1 | 127 | 23 | 14 | 17 | 22 | 51 | 12 |
| `degrowth` | negative_signal | negative_lean | -7.2 | ±5.0 | -8.5 | -7 | 124 | 13 | 13 | 16 | 20 | 62 | 14 |

## Raw-Status Misread Risks

These are claims where the raw `empirical_status` label points the opposite way from the school-level scoreboard outcome.

| school | claim | hypothesis | raw status | prediction | outcome |
| --- | ---: | --- | --- | --- | --- |
| `democratic_socialist` | 65 | `sweden_1990s_market_reform_recovery` | falsified | falsified | supports_position |
| `democratic_socialist` | 70 | `firm_entry_rate_long_run_productivity` | supported | falsified | refutes_position |
| `democratic_socialist` | 71 | `frontier_income_volatility_state_allocation` | falsified | falsified | supports_position |
| `developmentalism` | 130 | `bank_state_ownership_credit_misallocation` | falsified | falsified | supports_position |
| `developmentalism` | 131 | `venture_capital_market_depth_innovation` | falsified | falsified | supports_position |
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

## Left-Cluster Readout

- `degrowth`: signal=negative_signal; lean=negative_lean; q-net=-7.2; raw-net=-8.5; q-band=±5.0; supports=13; partial+=13; partial-=16; refutes=20; neutral=62; untested=14.
- `eco_socialist`: signal=too_close_to_call; lean=negative_lean; q-net=-4.1; raw-net=1.5; q-band=±5.0; supports=26; partial+=15; partial-=16; refutes=24; neutral=47; untested=16.
- `democratic_socialist`: signal=too_close_to_call; lean=negative_lean; q-net=-3.4; raw-net=1.5; q-band=±5.0; supports=22; partial+=16; partial-=17; refutes=20; neutral=47; untested=17.
- `market_socialist`: signal=too_close_to_call; lean=negative_lean; q-net=-2.4; raw-net=4.5; q-band=±5.0; supports=24; partial+=15; partial-=16; refutes=19; neutral=48; untested=16.
- `marxian`: signal=too_close_to_call; lean=negative_lean; q-net=-1.4; raw-net=3.0; q-band=±5.0; supports=25; partial+=16; partial-=16; refutes=22; neutral=46; untested=14.
- `marxist_leninist`: signal=too_close_to_call; lean=negative_lean; q-net=-1.6; raw-net=4.0; q-band=±5.0; supports=21; partial+=16; partial-=18; refutes=16; neutral=49; untested=15.
- `mmt`: signal=too_close_to_call; lean=negative_lean; q-net=-2.1; raw-net=3.5; q-band=±5.0; supports=26; partial+=11; partial-=16; refutes=20; neutral=51; untested=12.
- `post_keynesian`: signal=too_close_to_call; lean=negative_lean; q-net=-0.2; raw-net=6.5; q-band=±5.0; supports=28; partial+=12; partial-=17; refutes=19; neutral=48; untested=12.
- `social_democratic`: signal=too_close_to_call; lean=negative_lean; q-net=-4.4; raw-net=-0.5; q-band=±5.0; supports=23; partial+=14; partial-=17; refutes=22; neutral=51; untested=12.

## Marxist-Cluster Readout

- `marxian`: signal=too_close_to_call; q-net=-1.4; raw-net=3.0; q-band=±5.0; supports=25; partial+=16; partial-=16; refutes=22; neutral=46; untested=14.
- `marxist_leninist`: signal=too_close_to_call; q-net=-1.6; raw-net=4.0; q-band=±5.0; supports=21; partial+=16; partial-=18; refutes=16; neutral=49; untested=15.
