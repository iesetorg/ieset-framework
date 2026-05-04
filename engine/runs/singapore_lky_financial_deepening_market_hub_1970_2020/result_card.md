# Result card - singapore_lky_financial_deepening_market_hub_1970_2020

**Verdict:** SUPPORTED - 4 of 4 metrics met threshold (support threshold 3)

## Pre-registration
- **Claim:** Singapore's LKY-era market-rule and financial-hub trajectory produced deep private credit, large FDI intensity, and high market-rule scores by the modern endpoint, consistent with an open financial-services hub rather than a closed developmental state.
- **Falsification rule:** SUPPORTED if at least 3 of 4 metrics meet their thresholds; REFUTED if at most 1 meet after available data are evaluated.
- **Falsification test:** singapore_lky_financial_deepening_market_hub_1970_2020_local_multimetric_checklist

## Metric Results
| metric | observed | threshold | status | note |
|---|---:|---|---|---|
| private_credit_depth_gain | 83.879 | >= 70pp increase | MET | SGP private credit/GDP change = 83.879; threshold >= 70 |
| private_credit_depth_2020 | 129.191 | >= 100% of GDP | MET | SGP private credit/GDP 2020 = 129.191; threshold >= 100 |
| fdi_intensity_1990_2024 | 18.455 | >= 15% of GDP mean | MET | SGP FDI/GDP mean 1990-2024 = 18.455; threshold >= 15 |
| efw_market_rules_2023 | 8.500 | >= 8.0 | MET | SGP EFW summary 2023 = 8.500; threshold >= 8 |

## Interpretation
This is a pre-registered descriptive checklist over local vintages. It grades whether the observed case pattern clears the stated thresholds; it does not identify a single causal lever inside the policy bundle.

## Sources
- `world_bank_wdi:FS.AST.PRVT.GD.ZS` -> `data/vintages/world_bank_wdi/FS.AST.PRVT.GD.ZS@2026-04-30T140120Z.parquet`
- `world_bank_wdi:BX.KLT.DINV.WD.GD.ZS` -> `data/vintages/world_bank_wdi/BX.KLT.DINV.WD.GD.ZS@2026-04-30T140100Z.parquet`
- `fraser_efw:summary_index` -> `data/vintages/fraser_efw/summary_index@2026-05-02T220000Z.parquet`

## Steelman
See `hypotheses/steelman/singapore_lky_financial_deepening_market_hub_1970_2020.md`.
