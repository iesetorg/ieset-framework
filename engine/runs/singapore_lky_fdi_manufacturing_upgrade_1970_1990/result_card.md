# Result card - singapore_lky_fdi_manufacturing_upgrade_1970_1990

**Verdict:** SUPPORTED - 4 of 4 metrics met threshold (support threshold 3)

## Pre-registration
- **Claim:** Singapore's LKY-era industrial strategy worked through disciplined openness to foreign capital and manufacturing upgrading: FDI inflows were persistently high, FDI intensity exceeded regional peers, manufacturing value added rose sharply, and manufactured exports dominated by 1990.
- **Falsification rule:** SUPPORTED if at least 3 of 4 metrics meet their thresholds; REFUTED if at most 1 meet after available data are evaluated.
- **Falsification test:** singapore_lky_fdi_manufacturing_upgrade_1970_1990_local_multimetric_checklist

## Metric Results
| metric | observed | threshold | status | note |
|---|---:|---|---|---|
| fdi_intensity_mean | 8.129 | >= 5% of GDP | MET | SGP FDI/GDP mean = 8.129; threshold >= 5 |
| fdi_vs_peer_median_1990 | 7.884 | >= 3.0x peer median | MET | SGP 1990 FDI/GDP / peer median = 7.884; threshold >= 3 |
| manufacturing_va_share_gain | 12.989 | >= 10pp increase | MET | SGP manufacturing VA share change = 12.989; threshold >= 10 |
| manufactured_exports_share_1990 | 71.115 | >= 60% of merchandise exports | MET | SGP manufactured exports share 1990 = 71.115; threshold >= 60 |

## Interpretation
This is a pre-registered descriptive checklist over local vintages. It grades whether the observed Singapore pattern clears the stated thresholds; it does not identify a single causal lever inside the LKY-era bundle.

## Sources
- `world_bank_wdi:BX.KLT.DINV.WD.GD.ZS` -> `data/vintages/world_bank_wdi/BX.KLT.DINV.WD.GD.ZS@2026-05-05T195106Z.parquet`
- `world_bank_wdi:NV.IND.MANF.ZS` -> `data/vintages/world_bank_wdi/NV.IND.MANF.ZS@2026-05-05T194954Z.parquet`
- `world_bank_wdi:TX.VAL.MANF.ZS.UN` -> `data/vintages/world_bank_wdi/TX.VAL.MANF.ZS.UN@2026-04-30T115209Z.parquet`

## Steelman
See `hypotheses/steelman/singapore_lky_fdi_manufacturing_upgrade_1970_1990.md`.
