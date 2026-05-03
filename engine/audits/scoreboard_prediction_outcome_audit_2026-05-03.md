# Scoreboard Prediction-Outcome Audit

Generated: 2026-05-03

## Methodology Gate

- School outcomes are computed from `verdict + school_prediction + polarity`.
- Raw `empirical_status` is a hypothesis-verdict label, not automatically a school win.
- `SUPPORTED` refutes a school that predicted `falsified`; `REFUTED` supports that school.
- Directional partials count half-weight; neutral partials do not move net score.

## Ranked School Outcomes

| school | net | tested | supports | partial + | partial - | refutes | neutral | untested |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `classical_liberal` | 42.0 | 110 | 30 | 59 | 1 | 17 | 3 | 44 |
| `ordoliberal` | 42.0 | 97 | 26 | 56 | 0 | 12 | 3 | 45 |
| `austrian` | 33.5 | 86 | 25 | 43 | 0 | 13 | 5 | 44 |
| `empirical_pragmatist` | 23.0 | 82 | 11 | 34 | 0 | 5 | 32 | 45 |
| `chicago_monetarism` | 21.5 | 56 | 18 | 25 | 0 | 9 | 4 | 47 |
| `developmentalism` | 15.0 | 58 | 16 | 6 | 0 | 4 | 32 | 67 |
| `institutionalism` | 12.5 | 59 | 5 | 23 | 0 | 4 | 27 | 47 |
| `new_keynesian` | 4.5 | 50 | 7 | 7 | 0 | 6 | 30 | 39 |
| `social_democratic` | -2.5 | 50 | 12 | 8 | 15 | 11 | 4 | 48 |
| `eco_socialist` | -4.5 | 36 | 10 | 1 | 12 | 9 | 4 | 33 |
| `post_keynesian` | -5.0 | 43 | 11 | 3 | 15 | 10 | 4 | 32 |
| `mmt` | -7.5 | 29 | 6 | 1 | 12 | 8 | 2 | 34 |
| `degrowth` | -8.0 | 35 | 6 | 2 | 12 | 9 | 6 | 29 |
| `marxist_leninist` | -9.0 | 39 | 6 | 4 | 16 | 9 | 4 | 33 |
| `market_socialist` | -9.5 | 31 | 5 | 3 | 12 | 10 | 1 | 33 |
| `marxian` | -10.0 | 31 | 5 | 2 | 12 | 10 | 2 | 35 |
| `democratic_socialist` | -11.5 | 37 | 6 | 4 | 15 | 12 | 0 | 36 |

## Raw-Status Misread Risks

These are claims where the raw `empirical_status` label points the opposite way from the school-level scoreboard outcome.

| school | claim | hypothesis | raw status | prediction | outcome |
| --- | ---: | --- | --- | --- | --- |
| `democratic_socialist` | 65 | `sweden_1990s_market_reform_recovery` | falsified | falsified | supports_position |
| `democratic_socialist` | 70 | `firm_entry_rate_long_run_productivity` | supported | falsified | refutes_position |
| `democratic_socialist` | 71 | `frontier_income_volatility_state_allocation` | falsified | falsified | supports_position |
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

- `marxian`: net=-10.0; supports=5; partial+=2; partial-=12; refutes=10; neutral=2; untested=35.
- `marxist_leninist`: net=-9.0; supports=6; partial+=4; partial-=16; refutes=9; neutral=4; untested=33.
