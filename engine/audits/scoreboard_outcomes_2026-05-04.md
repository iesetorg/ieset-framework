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
| `ordoliberal` | 59.0 | 132 | 34 | 80 | 0 | 15 | 3 | 10 |
| `classical_liberal` | 54.5 | 145 | 37 | 78 | 3 | 20 | 7 | 10 |
| `austrian` | 45.0 | 124 | 31 | 61 | 1 | 16 | 15 | 6 |
| `chicago_monetarism` | 45.0 | 122 | 32 | 50 | 2 | 11 | 27 | 8 |
| `developmentalism` | 41.5 | 122 | 41 | 11 | 0 | 5 | 65 | 8 |
| `empirical_pragmatist` | 27.5 | 122 | 13 | 43 | 0 | 7 | 59 | 9 |
| `institutionalism` | 24.0 | 122 | 12 | 36 | 0 | 6 | 68 | 11 |
| `new_keynesian` | 16.0 | 122 | 14 | 18 | 0 | 7 | 83 | 10 |
| `eco_socialist` | 0.5 | 122 | 24 | 25 | 30 | 21 | 22 | 13 |
| `mmt` | -2.0 | 122 | 24 | 18 | 30 | 20 | 30 | 10 |
| `post_keynesian` | -2.0 | 122 | 23 | 26 | 34 | 21 | 18 | 9 |
| `social_democratic` | -2.0 | 122 | 21 | 28 | 30 | 22 | 21 | 11 |
| `market_socialist` | -4.0 | 122 | 21 | 26 | 30 | 23 | 22 | 12 |
| `degrowth` | -4.5 | 122 | 13 | 22 | 23 | 17 | 47 | 11 |
| `marxist_leninist` | -5.5 | 122 | 21 | 23 | 36 | 20 | 22 | 13 |
| `marxian` | -8.0 | 122 | 20 | 25 | 31 | 25 | 21 | 12 |
| `democratic_socialist` | -8.5 | 122 | 20 | 25 | 34 | 24 | 19 | 15 |

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

- `marxian`: net=-8.0; supports=20; partial+=25; partial-=31; refutes=25; neutral=21; untested=12.
- `marxist_leninist`: net=-5.5; supports=21; partial+=23; partial-=36; refutes=20; neutral=22; untested=13.
