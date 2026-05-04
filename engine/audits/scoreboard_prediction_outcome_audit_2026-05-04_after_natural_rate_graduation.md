# Scoreboard Prediction-Outcome Audit

Generated: 2026-05-05

## Methodology Gate

- School outcomes are computed from `verdict + school_prediction + polarity`.
- Raw `empirical_status` is a hypothesis-verdict label, not automatically a school win.
- `SUPPORTED` refutes a school that predicted `falsified`; `REFUTED` supports that school.
- Directional partials count half-weight; neutral partials do not move net score.

## Ranked School Outcomes

| school | net | tested | supports | partial + | partial - | refutes | neutral | untested |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `ordoliberal` | 61.0 | 134 | 34 | 82 | 0 | 14 | 4 | 8 |
| `classical_liberal` | 55.0 | 146 | 36 | 80 | 4 | 19 | 7 | 9 |
| `austrian` | 45.5 | 124 | 31 | 61 | 2 | 15 | 15 | 6 |
| `chicago_monetarism` | 44.0 | 122 | 32 | 49 | 3 | 11 | 27 | 8 |
| `developmentalism` | 42.5 | 122 | 41 | 12 | 1 | 4 | 64 | 8 |
| `empirical_pragmatist` | 28.0 | 123 | 12 | 46 | 0 | 7 | 58 | 8 |
| `institutionalism` | 25.0 | 123 | 12 | 38 | 0 | 6 | 67 | 10 |
| `new_keynesian` | 16.5 | 122 | 14 | 19 | 0 | 7 | 82 | 10 |
| `eco_socialist` | 1.5 | 122 | 24 | 26 | 29 | 21 | 22 | 13 |
| `mmt` | -1.0 | 122 | 24 | 19 | 29 | 20 | 30 | 10 |
| `post_keynesian` | -1.5 | 121 | 23 | 26 | 33 | 21 | 18 | 10 |
| `social_democratic` | -2.0 | 123 | 20 | 30 | 30 | 22 | 21 | 10 |
| `market_socialist` | -3.0 | 122 | 21 | 27 | 29 | 23 | 22 | 12 |
| `marxist_leninist` | -4.5 | 122 | 21 | 24 | 35 | 20 | 22 | 13 |
| `degrowth` | -5.0 | 122 | 12 | 23 | 23 | 17 | 47 | 11 |
| `marxian` | -7.0 | 122 | 20 | 26 | 30 | 25 | 21 | 12 |
| `democratic_socialist` | -7.5 | 122 | 20 | 26 | 33 | 24 | 19 | 15 |

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

- `marxian`: net=-7.0; supports=20; partial+=26; partial-=30; refutes=25; neutral=21; untested=12.
- `marxist_leninist`: net=-4.5; supports=21; partial+=24; partial-=35; refutes=20; neutral=22; untested=13.
