# Result card - singapore_lky_rule_of_law_government_effectiveness_legacy_1996_2024

**Verdict:** SUPPORTED - 4 of 4 metrics met threshold (support threshold 3)

## Pre-registration
- **Claim:** Singapore's post-LKY institutional legacy is visible in WGI data: control of corruption, government effectiveness, and rule of law remain near the top of the regional peer set from 1996 to 2024. This is a legacy pattern, not a direct causal test of Lee Kuan Yew's premiership.
- **Falsification rule:** SUPPORTED if at least 3 of 4 metrics meet their thresholds; REFUTED if at most 1 meet after available data are evaluated.
- **Falsification test:** singapore_lky_rule_of_law_government_effectiveness_legacy_1996_2024_local_multimetric_checklist

## Metric Results
| metric | observed | threshold | status | note |
|---|---:|---|---|---|
| control_corruption_mean | 2.062 | >= 1.75 | MET | SGP WGI CC mean = 2.062; threshold >= 1.75 |
| government_effectiveness_mean | 2.211 | >= 2.00 | MET | SGP WGI GE mean = 2.211; threshold >= 2 |
| rule_of_law_mean | 1.464 | >= 1.25 | MET | SGP WGI RL mean = 1.464; threshold >= 1.25 |
| corruption_control_peer_gap_2024 | 1.983 | >= 1.0 point above peer median | MET | SGP 2024 CC minus peer median = 1.983; threshold >= 1 |

## Interpretation
This is a pre-registered descriptive checklist over local vintages. It grades whether the observed Singapore pattern clears the stated thresholds; it does not identify a single causal lever inside the LKY-era bundle.

## Sources
- `wgi:CC.EST` -> `data/vintages/wgi/CC.EST@2026-04-30T114239Z.parquet`
- `wgi:GE.EST` -> `data/vintages/wgi/GE.EST@2026-04-30T114242Z.parquet`
- `wgi:RL.EST` -> `data/vintages/wgi/RL.EST@2026-04-30T114245Z.parquet`

## Steelman
See `hypotheses/steelman/singapore_lky_rule_of_law_government_effectiveness_legacy_1996_2024.md`.
