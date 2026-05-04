# Result card - uae_oil_rent_diversification_services_1990_2024

**Verdict:** SUPPORTED - 4 of 4 metrics met threshold (support threshold 3)

## Pre-registration
- **Claim:** The UAE diversification model reduced direct oil-rent dependence and expanded services, while still retaining hydrocarbon-export exposure. The claim is deliberately two-sided: support requires services and oil-rent metrics to improve, but fuel-export dependence remains a risk metric.
- **Falsification rule:** SUPPORTED if at least 3 of 4 metrics meet their thresholds; REFUTED if at most 1 meet after available data are evaluated.
- **Falsification test:** uae_oil_rent_diversification_services_1990_2024_local_multimetric_checklist

## Metric Results
| metric | observed | threshold | status | note |
|---|---:|---|---|---|
| oil_rents_share_decline | 19.643 | >= 15pp decline | MET | ARE oil rents/GDP decline = 19.643; threshold >= 15 |
| services_va_share_gain | 14.862 | >= 10pp increase | MET | ARE services VA share change = 14.862; threshold >= 10 |
| fuel_exports_share_decline_post_2000 | 25.641 | >= 15pp decline | MET | ARE fuel exports share decline 2000-2023 = 25.641; threshold >= 15 |
| trade_openness_mean | 147.634 | >= 140% of GDP mean | MET | ARE trade/GDP mean = 147.634; threshold >= 140 |

## Interpretation
This is a pre-registered descriptive checklist over local vintages. It grades whether the observed case pattern clears the stated thresholds; it does not identify a single causal lever inside the policy bundle.

## Sources
- `world_bank_wdi:NY.GDP.PETR.RT.ZS` -> `data/vintages/world_bank_wdi/NY.GDP.PETR.RT.ZS@2026-04-30T115050Z.parquet`
- `world_bank_wdi:NV.SRV.TOTL.ZS` -> `data/vintages/world_bank_wdi/NV.SRV.TOTL.ZS@2026-04-30T140038Z.parquet`
- `world_bank_wdi:TX.VAL.FUEL.ZS.UN` -> `data/vintages/world_bank_wdi/TX.VAL.FUEL.ZS.UN@2026-04-30T115204Z.parquet`
- `world_bank_wdi:NE.TRD.GNFS.ZS` -> `data/vintages/world_bank_wdi/NE.TRD.GNFS.ZS@2026-04-30T135618Z.parquet`

## Steelman
See `hypotheses/steelman/uae_oil_rent_diversification_services_1990_2024.md`.
