# Result card - singapore_lky_changi_air_hub_tourism_1981_2019

**Verdict:** SUPPORTED - 4 of 4 metrics met threshold (support threshold 3)

## Pre-registration
- **Claim:** Singapore's Changi airport, SIA, port-state, and open-city strategy produced a durable air-services and visitor hub: by the pre-COVID endpoint, tourist arrivals were multiple times resident population, receipts were material, and the same economy remained extremely trade-open.
- **Falsification rule:** SUPPORTED if at least 3 of 4 metrics meet their thresholds; REFUTED if at most 1 meet after available data are evaluated.
- **Falsification test:** singapore_lky_changi_air_hub_tourism_1981_2019_local_multimetric_checklist

## Metric Results
| metric | observed | threshold | status | note |
|---|---:|---|---|---|
| visitor_arrivals_2019 | 19116000.000 | >= 15 million | MET | SGP tourist arrivals 2019 = 19116000.000; threshold >= 1.5e+07 |
| visitor_arrivals_per_capita_2019 | 3.352 | >= 3.0 arrivals per resident | MET | SGP visitor arrivals per resident 2019 = 3.352; threshold >= 3 |
| tourism_receipts_export_share | 3.011 | >= 2% of exports mean | MET | SGP tourism receipts / exports mean = 3.011; threshold >= 2 |
| trade_openness_2019 | 324.395 | >= 300% of GDP | MET | SGP trade/GDP 2019 = 324.395; threshold >= 300 |

## Interpretation
This is a pre-registered descriptive checklist over local vintages. It grades whether the observed case pattern clears the stated thresholds; it does not identify a single causal lever inside the policy bundle.

## Sources
- `world_bank_wdi:ST.INT.ARVL` -> `data/vintages/world_bank_wdi/ST.INT.ARVL@2026-04-30T130312Z.parquet`
- `world_bank_wdi:SP.POP.TOTL` -> `data/vintages/world_bank_wdi/SP.POP.TOTL@2026-04-30T135559Z.parquet`
- `world_bank_wdi:ST.INT.RCPT.XP.ZS` -> `data/vintages/world_bank_wdi/ST.INT.RCPT.XP.ZS@2026-04-30T130334Z.parquet`
- `world_bank_wdi:NE.TRD.GNFS.ZS` -> `data/vintages/world_bank_wdi/NE.TRD.GNFS.ZS@2026-04-30T135618Z.parquet`

## Steelman
See `hypotheses/steelman/singapore_lky_changi_air_hub_tourism_1981_2019.md`.
