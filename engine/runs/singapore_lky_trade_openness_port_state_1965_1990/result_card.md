# Result card - singapore_lky_trade_openness_port_state_1965_1990

**Verdict:** SUPPORTED - 4 of 4 metrics met threshold (support threshold 3)

## Pre-registration
- **Claim:** The LKY-era Singapore model was extraordinarily trade-open rather than autarkic: trade and exports were far above GDP, trade openness beat regional peers, and manufactured exports became a dominant share by 1990.
- **Falsification rule:** SUPPORTED if at least 3 of 4 metrics meet their thresholds; REFUTED if at most 1 meet after available data are evaluated.
- **Falsification test:** singapore_lky_trade_openness_port_state_1965_1990_local_multimetric_checklist

## Metric Results
| metric | observed | threshold | status | note |
|---|---:|---|---|---|
| trade_openness_mean | 308.778 | >= 250% of GDP | MET | SGP trade/GDP mean = 308.778; threshold >= 250 |
| exports_share_mean | 152.044 | >= 120% of GDP | MET | SGP exports/GDP mean = 152.044; threshold >= 120 |
| trade_vs_peer_median_1990 | 5.352 | >= 2.0x peer median | MET | SGP 1990 trade/GDP / peer median = 5.352; threshold >= 2 |
| manufactured_exports_upgrade | 40.783 | >= 30pp increase | MET | SGP manufactured-export share change = 40.783; threshold >= 30 |

## Interpretation
This is a pre-registered descriptive checklist over local vintages. It grades whether the observed Singapore pattern clears the stated thresholds; it does not identify a single causal lever inside the LKY-era bundle.

## Sources
- `world_bank_wdi:NE.TRD.GNFS.ZS` -> `data/vintages/world_bank_wdi/NE.TRD.GNFS.ZS@2026-04-30T135618Z.parquet`
- `world_bank_wdi:NE.EXP.GNFS.ZS` -> `data/vintages/world_bank_wdi/NE.EXP.GNFS.ZS@2026-04-30T130354Z.parquet`
- `world_bank_wdi:TX.VAL.MANF.ZS.UN` -> `data/vintages/world_bank_wdi/TX.VAL.MANF.ZS.UN@2026-04-30T115209Z.parquet`

## Steelman
See `hypotheses/steelman/singapore_lky_trade_openness_port_state_1965_1990.md`.
