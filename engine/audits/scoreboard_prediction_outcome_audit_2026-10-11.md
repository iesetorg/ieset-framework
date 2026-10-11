# Scoreboard Prediction-Outcome Audit

Generated: 2026-10-11

## Methodology Gate

- School outcomes are computed from `verdict + school_prediction + polarity`.
- Raw `empirical_status` is a hypothesis-verdict label, not automatically a school win.
- `SUPPORTED` refutes a school that predicted `falsified`; `REFUTED` supports that school.
- Directional partials count half-weight; neutral partials do not move net score.
- Tiny aggregate margins are a no-call: `abs(net) <= max(5, 5% of tested)` is `too_close_to_call`.
- The audit keeps a separate signed lean so no-call rows still show whether the net is positive, negative, or flat.
- Q-net discounts lower-identification evidence: causal=1.0, associational=0.5, descriptive/canonical=0.25.
- Benchmark-control rows are computed for calibration but excluded from ranked school outcomes.
- Public calibration links with `school_score_eligible=false` remain listed but are untested for all schools.
- School predictions first attached or changed after a study's first run remain visible as historical links but are excluded from advance forecast scoring.

## Ranked School Outcomes

| school | lean | q-net | q-band | raw net | decisive net | tested | supports | partial + | partial - | refutes | neutral | untested |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `austrian` | positive_lean | 4.0 | ±5.0 | 8.0 | 8 | 40 | 12 | 0 | 0 | 4 | 24 | 259 |
| `ordoliberal` | positive_lean | 3.5 | ±5.0 | 7.0 | 7 | 52 | 12 | 0 | 0 | 5 | 35 | 268 |
| `classical_liberal` | positive_lean | 3.0 | ±5.0 | 6.0 | 6 | 53 | 12 | 0 | 0 | 6 | 35 | 301 |
| `chicago_monetarism` | positive_lean | 0.5 | ±5.0 | 1.0 | 1 | 14 | 5 | 0 | 0 | 4 | 5 | 287 |
| `mmt` | positive_lean | 0.5 | ±5.0 | 1.0 | 1 | 1 | 1 | 0 | 0 | 0 | 0 | 285 |
| `degrowth` | untested | 0.0 | ±0.0 | 0.0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 289 |
| `democratic_socialist` | untested | 0.0 | ±0.0 | 0.0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 287 |
| `developmentalism` | untested | 0.0 | ±0.0 | 0.0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 301 |
| `eco_socialist` | untested | 0.0 | ±0.0 | 0.0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 292 |
| `marxian` | untested | 0.0 | ±0.0 | 0.0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 290 |
| `marxist_leninist` | untested | 0.0 | ±0.0 | 0.0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 283 |
| `new_keynesian` | untested | 0.0 | ±0.0 | 0.0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 286 |
| `post_keynesian` | untested | 0.0 | ±0.0 | 0.0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 285 |
| `institutionalism` | negative_lean | -0.5 | ±5.0 | -1.0 | -1 | 12 | 0 | 0 | 0 | 1 | 11 | 281 |
| `market_socialist` | negative_lean | -0.5 | ±5.0 | -1.0 | -1 | 1 | 0 | 0 | 0 | 1 | 0 | 287 |
| `social_democratic` | negative_lean | -0.5 | ±5.0 | -1.0 | -1 | 1 | 0 | 0 | 0 | 1 | 0 | 301 |

## Benchmark Control Readout

These rows are calibration/house-position controls. They are not ranked as ideological schools.

| control | lean | q-net | q-band | raw net | decisive net | tested | supports | partial + | partial - | refutes | neutral | untested |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `empirical_pragmatist` | flat | 0.0 | ±5.0 | 0.0 | 0 | 28 | 2 | 0 | 0 | 2 | 24 | 283 |

## Raw-Status Misread Risks

These are claims where the raw `empirical_status` label points the opposite way from the school-level scoreboard outcome.

| school | claim | hypothesis | raw status | prediction | outcome |
| --- | ---: | --- | --- | --- | --- |
| `market_socialist` | 138 | `bls_qcew_county_food_service_minimum_wage_growth` | supported | falsified | refutes_position |
| `social_democratic` | 148 | `oecd_low_education_unemployment_minimum_wage_bite` | supported | falsified | refutes_position |

## Left-Cluster Readout

- `degrowth`: signal=untested; lean=untested; q-net=0.0; raw-net=0.0; q-band=±0.0; supports=0; partial+=0; partial-=0; refutes=0; neutral=0; untested=289.
- `eco_socialist`: signal=untested; lean=untested; q-net=0.0; raw-net=0.0; q-band=±0.0; supports=0; partial+=0; partial-=0; refutes=0; neutral=0; untested=292.
- `democratic_socialist`: signal=untested; lean=untested; q-net=0.0; raw-net=0.0; q-band=±0.0; supports=0; partial+=0; partial-=0; refutes=0; neutral=0; untested=287.
- `market_socialist`: signal=too_close_to_call; lean=negative_lean; q-net=-0.5; raw-net=-1.0; q-band=±5.0; supports=0; partial+=0; partial-=0; refutes=1; neutral=0; untested=287.
- `marxian`: signal=untested; lean=untested; q-net=0.0; raw-net=0.0; q-band=±0.0; supports=0; partial+=0; partial-=0; refutes=0; neutral=0; untested=290.
- `marxist_leninist`: signal=untested; lean=untested; q-net=0.0; raw-net=0.0; q-band=±0.0; supports=0; partial+=0; partial-=0; refutes=0; neutral=0; untested=283.
- `mmt`: signal=too_close_to_call; lean=positive_lean; q-net=0.5; raw-net=1.0; q-band=±5.0; supports=1; partial+=0; partial-=0; refutes=0; neutral=0; untested=285.
- `post_keynesian`: signal=untested; lean=untested; q-net=0.0; raw-net=0.0; q-band=±0.0; supports=0; partial+=0; partial-=0; refutes=0; neutral=0; untested=285.
- `social_democratic`: signal=too_close_to_call; lean=negative_lean; q-net=-0.5; raw-net=-1.0; q-band=±5.0; supports=0; partial+=0; partial-=0; refutes=1; neutral=0; untested=301.

## Marxist-Cluster Readout

- `marxian`: signal=untested; q-net=0.0; raw-net=0.0; q-band=±0.0; supports=0; partial+=0; partial-=0; refutes=0; neutral=0; untested=290.
- `marxist_leninist`: signal=untested; q-net=0.0; raw-net=0.0; q-band=±0.0; supports=0; partial+=0; partial-=0; refutes=0; neutral=0; untested=283.
