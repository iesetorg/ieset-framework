# Result card - singapore_lky_public_health_outcomes_1965_1990

**Verdict:** SUPPORTED - 4 of 4 metrics met threshold (support threshold 3)

## Pre-registration
- **Claim:** Singapore's Lee Kuan Yew era public-health and disciplined social-policy bundle coincided with first-world health outcome convergence by 1990: life expectancy rose strongly, infant mortality collapsed, and Singapore beat regional market-economy peers on both endpoints.
- **Falsification rule:** SUPPORTED if at least 3 of 4 metrics meet their thresholds; REFUTED if at most 1 meet after available data are evaluated.
- **Falsification test:** singapore_lky_public_health_outcomes_1965_1990_local_multimetric_checklist

## Metric Results
| metric | observed | threshold | status | note |
|---|---:|---|---|---|
| life_expectancy_gain | 8.062 | >= 7 years | MET | SGP life expectancy gain = 8.062; threshold >= 7 |
| infant_mortality_drop | 21.200 | >= 20 deaths per 1,000 live births decline | MET | SGP infant mortality decline = 21.200; threshold >= 20 |
| life_expectancy_peer_gap_1990 | 5.357 | >= 4 years above peer median | MET | SGP life expectancy minus Asian peer median = 5.357; threshold >= 4 |
| infant_mortality_peer_ratio_1990 | 0.197 | <= 0.50x peer median | MET | SGP infant mortality / Asian peer median = 0.197; threshold <= 0.5 |

## Interpretation
This is a pre-registered descriptive checklist over local vintages. It grades whether the observed case pattern clears the stated thresholds; it does not identify a single causal lever inside the policy bundle.

## Sources
- `world_bank_wdi:SP.DYN.LE00.IN` -> `data/vintages/world_bank_wdi/SP.DYN.LE00.IN@2026-04-30T140038Z.parquet`
- `world_bank_wdi:SP.DYN.IMRT.IN` -> `data/vintages/world_bank_wdi/SP.DYN.IMRT.IN@2026-04-30T114634Z.parquet`

## Steelman
See `hypotheses/steelman/singapore_lky_public_health_outcomes_1965_1990.md`.
