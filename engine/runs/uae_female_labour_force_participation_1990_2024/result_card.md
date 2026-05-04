# Result card - uae_female_labour_force_participation_1990_2024

**Verdict:** SUPPORTED - 4 of 4 metrics met threshold (support threshold 3)

## Pre-registration
- **Claim:** The UAE's education, migration, and labour-market reforms were followed by a large rise in female labour-force participation, placing the UAE above the GCC peer median by the 2020s.
- **Falsification rule:** SUPPORTED if at least 3 of 4 metrics meet their thresholds; REFUTED if at most 1 meet after available data are evaluated.
- **Falsification test:** uae_female_labour_force_participation_1990_2024_local_multimetric_checklist

## Metric Results
| metric | observed | threshold | status | note |
|---|---:|---|---|---|
| female_lfp_gain | 23.199 | >= 20pp increase | MET | ARE female LFP change = 23.199; threshold >= 20 |
| female_lfp_2024 | 52.519 | >= 50% | MET | ARE female LFP 2024 = 52.519; threshold >= 50 |
| female_lfp_peer_gap_2024 | 10.113 | >= 8pp above peer median | MET | ARE female LFP minus GCC median = 10.113; threshold >= 8 |
| female_lfp_peer_ratio_2024 | 1.238 | >= 1.15x peer median | MET | ARE female LFP / GCC median = 1.238; threshold >= 1.15 |

## Interpretation
This is a pre-registered descriptive checklist over local vintages. It grades whether the observed case pattern clears the stated thresholds; it does not identify a single causal lever inside the policy bundle.

## Sources
- `world_bank_wdi:SL.TLF.CACT.FE.ZS` -> `data/vintages/world_bank_wdi/SL.TLF.CACT.FE.ZS@2026-04-30T140140Z.parquet`

## Steelman
See `hypotheses/steelman/uae_female_labour_force_participation_1990_2024.md`.
