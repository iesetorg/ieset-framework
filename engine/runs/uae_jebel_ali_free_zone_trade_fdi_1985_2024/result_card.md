# Result card - uae_jebel_ali_free_zone_trade_fdi_1985_2024

**Verdict:** SUPPORTED - 4 of 4 metrics met threshold (support threshold 3)

## Pre-registration
- **Claim:** The UAE's Jebel Ali and free-zone strategy produced a highly open trade and investment platform by Gulf standards: trade intensity is high, exceeds the GCC peer median, FDI intensity has become material, and trade-freedom scores remain high.
- **Falsification rule:** SUPPORTED if at least 3 of 4 metrics meet their thresholds; REFUTED if at most 1 meet after available data are evaluated.
- **Falsification test:** uae_jebel_ali_free_zone_trade_fdi_1985_2024_local_multimetric_checklist

## Metric Results
| metric | observed | threshold | status | note |
|---|---:|---|---|---|
| trade_openness_mean | 147.634 | >= 120% of GDP | MET | ARE trade/GDP mean = 147.634; threshold >= 120 |
| trade_openness_vs_gcc_2023 | 1.986 | >= 1.5x peer median | MET | ARE trade/GDP / GCC median 2023 = 1.986; threshold >= 1.5 |
| fdi_intensity_mature_endpoint | 8.263 | >= 5% of GDP | MET | ARE FDI/GDP 2024 = 8.263; threshold >= 5 |
| trade_freedom_score | 8.572 | >= 8.0 | MET | ARE EFW trade freedom 2023 = 8.572; threshold >= 8 |

## Interpretation
This is a pre-registered descriptive checklist over local vintages. It grades whether the observed case pattern clears the stated thresholds; it does not identify a single causal lever inside the policy bundle.

## Sources
- `world_bank_wdi:NE.TRD.GNFS.ZS` -> `data/vintages/world_bank_wdi/NE.TRD.GNFS.ZS@2026-04-30T135618Z.parquet`
- `world_bank_wdi:BX.KLT.DINV.WD.GD.ZS` -> `data/vintages/world_bank_wdi/BX.KLT.DINV.WD.GD.ZS@2026-04-30T140100Z.parquet`
- `fraser_efw:freedom_to_trade_internationally` -> `data/vintages/fraser_efw/freedom_to_trade_internationally@2026-05-02T220000Z.parquet`

## Steelman
See `hypotheses/steelman/uae_jebel_ali_free_zone_trade_fdi_1985_2024.md`.
