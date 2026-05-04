# Result card - singapore_lky_human_capital_upgrade_1965_2010

**Verdict:** SUPPORTED - 4 of 4 metrics met threshold (support threshold 3)

## Pre-registration
- **Claim:** Singapore's LKY-era and immediate post-LKY human-capital trajectory shows a large education upgrade: PWT human-capital index roughly doubled, upper-secondary attainment rose sharply, tertiary enrolment became mass-participation, and the 2010 human-capital level reached advanced-economy territory.
- **Falsification rule:** SUPPORTED if at least 3 of 4 metrics meet their thresholds; REFUTED if at most 1 meet after available data are evaluated.
- **Falsification test:** singapore_lky_human_capital_upgrade_1965_2010_local_multimetric_checklist

## Metric Results
| metric | observed | threshold | status | note |
|---|---:|---|---|---|
| pwt_hc_index_gain | 1.497 | >= 1.20 index points | MET | SGP PWT hc change = 1.497; threshold >= 1.2 |
| pwt_hc_index_ratio | 1.958 | >= 1.8x | MET | SGP PWT hc 2010/1965 = 1.958; threshold >= 1.8 |
| upper_secondary_attainment_gain | 48.602 | >= 35pp increase | MET | SGP upper-secondary attainment change = 48.602; threshold >= 35 |
| tertiary_enrolment_mass_participation | 93.270 | >= 70% | MET | SGP tertiary gross enrolment 2010 = 93.270; threshold >= 70 |

## Interpretation
This is a pre-registered descriptive checklist over local vintages. It grades whether the observed Singapore pattern clears the stated thresholds; it does not identify a single causal lever inside the LKY-era bundle.

## Sources
- `pwt:hc` -> `data/vintages/pwt/hc@2026-04-30T144523Z.parquet`
- `world_bank_wdi:SE.SEC.CUAT.UP.ZS` -> `data/vintages/world_bank_wdi/SE.SEC.CUAT.UP.ZS@2026-04-30T115107Z.parquet`
- `world_bank_wdi:SE.TER.ENRR` -> `data/vintages/world_bank_wdi/SE.TER.ENRR@2026-04-30T114614Z.parquet`

## Steelman
See `hypotheses/steelman/singapore_lky_human_capital_upgrade_1965_2010.md`.
