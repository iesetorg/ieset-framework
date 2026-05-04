# Scoreboard Prediction-Outcome Audit

Generated: 2026-05-04

## Methodology Gate

- School outcomes are computed from `verdict + school_prediction + polarity`.
- Raw `empirical_status` is a hypothesis-verdict label, not automatically a school win.
- `SUPPORTED` refutes a school that predicted `falsified`; `REFUTED` supports that school.
- Directional partials count half-weight; neutral partials do not move net score.

## Ranked School Outcomes

| school | net | tested | supports | partial + | partial - | refutes | neutral | untested |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `ordoliberal` | 60.5 | 135 | 35 | 81 | 0 | 15 | 4 | 7 |
| `classical_liberal` | 55.0 | 147 | 38 | 78 | 4 | 20 | 7 | 8 |
| `austrian` | 44.5 | 125 | 31 | 61 | 2 | 16 | 15 | 5 |
| `chicago_monetarism` | 44.0 | 122 | 32 | 49 | 3 | 11 | 27 | 8 |
| `developmentalism` | 42.0 | 123 | 41 | 12 | 0 | 5 | 65 | 7 |
| `empirical_pragmatist` | 28.5 | 124 | 13 | 45 | 0 | 7 | 59 | 7 |
| `institutionalism` | 25.5 | 124 | 13 | 37 | 0 | 6 | 68 | 9 |
| `new_keynesian` | 16.5 | 123 | 14 | 19 | 0 | 7 | 83 | 9 |
| `eco_socialist` | 2.5 | 123 | 25 | 26 | 29 | 21 | 22 | 12 |
| `mmt` | 0.0 | 123 | 25 | 19 | 29 | 20 | 30 | 9 |
| `post_keynesian` | -0.5 | 122 | 24 | 26 | 33 | 21 | 18 | 9 |
| `social_democratic` | -1.0 | 124 | 21 | 30 | 30 | 22 | 21 | 9 |
| `market_socialist` | -2.0 | 123 | 22 | 27 | 29 | 23 | 22 | 11 |
| `marxist_leninist` | -3.5 | 123 | 22 | 24 | 35 | 20 | 22 | 12 |
| `degrowth` | -4.0 | 123 | 13 | 23 | 23 | 17 | 47 | 10 |
| `marxian` | -6.0 | 123 | 21 | 26 | 30 | 25 | 21 | 11 |
| `democratic_socialist` | -6.5 | 123 | 21 | 26 | 33 | 24 | 19 | 14 |

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

- `marxian`: net=-6.0; supports=21; partial+=26; partial-=30; refutes=25; neutral=21; untested=11.
- `marxist_leninist`: net=-3.5; supports=22; partial+=24; partial-=35; refutes=20; neutral=22; untested=12.
