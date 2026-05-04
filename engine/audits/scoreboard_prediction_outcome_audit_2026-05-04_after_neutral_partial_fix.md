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
| `developmentalism` | 39.5 | 122 | 41 | 5 | 0 | 4 | 72 | 8 |
| `chicago_monetarism` | 35.0 | 122 | 32 | 29 | 1 | 11 | 49 | 8 |
| `ordoliberal` | 31.0 | 134 | 34 | 22 | 0 | 14 | 64 | 8 |
| `classical_liberal` | 27.5 | 146 | 36 | 22 | 1 | 19 | 68 | 9 |
| `austrian` | 27.5 | 124 | 31 | 23 | 0 | 15 | 55 | 6 |
| `new_keynesian` | 14.0 | 122 | 14 | 14 | 0 | 7 | 87 | 10 |
| `institutionalism` | 10.0 | 123 | 12 | 8 | 0 | 6 | 97 | 10 |
| `empirical_pragmatist` | 7.5 | 123 | 12 | 5 | 0 | 7 | 99 | 8 |
| `eco_socialist` | 3.0 | 122 | 24 | 16 | 16 | 21 | 45 | 13 |
| `mmt` | 2.0 | 122 | 24 | 12 | 16 | 20 | 50 | 10 |
| `marxist_leninist` | 0.5 | 122 | 21 | 17 | 18 | 20 | 46 | 13 |
| `post_keynesian` | 0.0 | 121 | 23 | 13 | 17 | 21 | 47 | 10 |
| `market_socialist` | -2.0 | 122 | 21 | 16 | 16 | 23 | 46 | 12 |
| `social_democratic` | -3.0 | 123 | 20 | 15 | 17 | 22 | 49 | 10 |
| `democratic_socialist` | -4.0 | 122 | 20 | 17 | 17 | 24 | 44 | 15 |
| `marxian` | -4.5 | 122 | 20 | 17 | 16 | 25 | 44 | 12 |
| `degrowth` | -6.0 | 122 | 12 | 14 | 16 | 17 | 63 | 11 |

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

- `marxian`: net=-4.5; supports=20; partial+=17; partial-=16; refutes=25; neutral=44; untested=12.
- `marxist_leninist`: net=0.5; supports=21; partial+=17; partial-=18; refutes=20; neutral=46; untested=13.
