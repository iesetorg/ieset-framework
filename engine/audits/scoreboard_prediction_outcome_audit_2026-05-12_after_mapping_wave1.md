# Scoreboard Prediction-Outcome Audit

Generated: 2026-05-12

## Methodology Gate

- School outcomes are computed from `verdict + school_prediction + polarity`.
- Raw `empirical_status` is a hypothesis-verdict label, not automatically a school win.
- `SUPPORTED` refutes a school that predicted `falsified`; `REFUTED` supports that school.
- Directional partials count half-weight; neutral partials do not move net score.
- Tiny aggregate margins are a no-call: `abs(net) < max(5, 5% of tested)` is `too_close_to_call`.
- Q-net discounts lower-identification evidence: causal=1.0, associational=0.5, descriptive/canonical=0.25.

## Ranked School Outcomes

| school | signal | q-net | q-band | raw net | decisive net | tested | supports | partial + | partial - | refutes | neutral | untested |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `chicago_monetarism` | positive_signal | 20.8 | ±5.0 | 34.5 | 20 | 124 | 32 | 30 | 1 | 12 | 49 | 8 |
| `ordoliberal` | positive_signal | 16.5 | ±5.0 | 28.0 | 17 | 139 | 35 | 22 | 0 | 18 | 64 | 8 |
| `austrian` | positive_signal | 16.2 | ±5.0 | 26.5 | 14 | 128 | 31 | 25 | 0 | 17 | 55 | 6 |
| `classical_liberal` | positive_signal | 15.2 | ±5.0 | 23.5 | 13 | 154 | 38 | 22 | 1 | 25 | 68 | 9 |
| `developmentalism` | positive_signal | 11.0 | ±5.0 | 41.5 | 39 | 124 | 43 | 5 | 0 | 4 | 72 | 9 |
| `new_keynesian` | too_close_to_call | 5.0 | ±5.0 | 13.5 | 7 | 119 | 14 | 13 | 0 | 7 | 85 | 13 |
| `empirical_pragmatist` | too_close_to_call | 4.8 | ±5.0 | 7.5 | 5 | 123 | 12 | 5 | 0 | 7 | 99 | 8 |
| `institutionalism` | too_close_to_call | 3.4 | ±5.0 | 10.0 | 6 | 122 | 12 | 8 | 0 | 6 | 96 | 11 |
| `mmt` | too_close_to_call | -1.1 | ±5.0 | 5.5 | 8 | 122 | 26 | 11 | 16 | 18 | 51 | 12 |
| `marxist_leninist` | too_close_to_call | -1.6 | ±5.0 | 4.0 | 5 | 120 | 21 | 16 | 18 | 16 | 49 | 15 |
| `post_keynesian` | too_close_to_call | -1.8 | ±5.0 | 3.5 | 6 | 121 | 25 | 12 | 17 | 19 | 48 | 12 |
| `eco_socialist` | too_close_to_call | -2.1 | ±5.0 | 5.5 | 6 | 120 | 24 | 15 | 16 | 18 | 47 | 16 |
| `marxian` | too_close_to_call | -2.9 | ±5.0 | 0.0 | 0 | 122 | 22 | 16 | 16 | 22 | 46 | 14 |
| `democratic_socialist` | too_close_to_call | -3.4 | ±5.0 | 1.5 | 2 | 122 | 22 | 16 | 17 | 20 | 47 | 17 |
| `social_democratic` | too_close_to_call | -3.4 | ±5.0 | 1.5 | 3 | 121 | 21 | 14 | 17 | 18 | 51 | 12 |
| `market_socialist` | too_close_to_call | -3.9 | ±5.0 | 1.5 | 2 | 119 | 21 | 15 | 16 | 19 | 48 | 16 |
| `degrowth` | too_close_to_call | -4.8 | ±5.0 | -3.5 | -2 | 119 | 13 | 13 | 16 | 15 | 62 | 14 |

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

## Marxist-Cluster Readout

- `marxian`: signal=too_close_to_call; q-net=-2.9; raw-net=0.0; q-band=±5.0; supports=22; partial+=16; partial-=16; refutes=22; neutral=46; untested=14.
- `marxist_leninist`: signal=too_close_to_call; q-net=-1.6; raw-net=4.0; q-band=±5.0; supports=21; partial+=16; partial-=18; refutes=16; neutral=49; untested=15.
