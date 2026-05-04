# Result card - uae_freezone_institutional_quality_wgi_1996_2024

**Verdict:** SUPPORTED - 3 of 4 metrics met threshold (support threshold 3)

## Pre-registration
- **Claim:** The UAE's free-zone, commercial-court, and state-capacity model is visible in relatively high government effectiveness, regulatory quality, rule-of-law, and market-rule scores compared with many resource-rent peers.
- **Falsification rule:** SUPPORTED if at least 3 of 4 metrics meet their thresholds; REFUTED if at most 1 meet after available data are evaluated.
- **Falsification test:** uae_freezone_institutional_quality_wgi_1996_2024_local_multimetric_checklist

## Metric Results
| metric | observed | threshold | status | note |
|---|---:|---|---|---|
| government_effectiveness_mean | 1.028 | >= 0.90 | MET | ARE WGI GE mean = 1.028; threshold >= 0.9 |
| regulatory_quality_mean | 0.913 | >= 0.75 | MET | ARE WGI RQ mean = 0.913; threshold >= 0.75 |
| rule_of_law_mean | 0.345 | >= 0.60 | NOT_MET | ARE WGI RL mean = 0.345; threshold >= 0.6 |
| efw_summary_2023 | 7.250 | >= 7.0 | MET | ARE EFW summary 2023 = 7.250; threshold >= 7 |

## Interpretation
This is a pre-registered descriptive checklist over local vintages. It grades whether the observed case pattern clears the stated thresholds; it does not identify a single causal lever inside the policy bundle.

## Sources
- `wgi:GE.EST` -> `data/vintages/wgi/GE.EST@2026-04-30T114242Z.parquet`
- `wgi:RQ.EST` -> `data/vintages/wgi/GOV_WGI_RQ.EST@2026-04-30T114234Z.parquet`
- `wgi:RL.EST` -> `data/vintages/wgi/RL.EST@2026-04-30T114245Z.parquet`
- `fraser_efw:summary_index` -> `data/vintages/fraser_efw/summary_index@2026-05-02T220000Z.parquet`

## Steelman
See `hypotheses/steelman/uae_freezone_institutional_quality_wgi_1996_2024.md`.
