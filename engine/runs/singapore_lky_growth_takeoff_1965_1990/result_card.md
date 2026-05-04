# Result card - singapore_lky_growth_takeoff_1965_1990

**Verdict:** SUPPORTED - 5 of 5 metrics met threshold (support threshold 4)

## Pre-registration
- **Claim:** Singapore's Lee Kuan Yew era growth takeoff from 1965 to 1990 was not a small city-state accounting artifact: real GDP per capita grew rapidly, the level multiplied several-fold, investment rates stayed high, and the 1990 income level exceeded regional market-economy peers by a large margin.
- **Falsification rule:** SUPPORTED if at least 4 of 5 metrics meet their thresholds; REFUTED if at most 2 meet after available data are evaluated.
- **Falsification test:** singapore_lky_growth_takeoff_1965_1990_local_multimetric_checklist

## Metric Results
| metric | observed | threshold | status | note |
|---|---:|---|---|---|
| real_gdp_pc_growth_avg | 7.053 | >= 5.0% | MET | SGP average GDP-pc growth 1965-1990 = 7.053; threshold >= 5 |
| real_gdp_pc_level_multiplier | 5.522 | >= 4.0x | MET | SGP GDP-pc 1990/1965 ratio = 5.522; threshold >= 4 |
| income_level_vs_peer_median_1990 | 6.829 | >= 3.0x peer median | MET | SGP 1990 GDP-pc / peer median = 6.829; threshold >= 3 |
| investment_share_high | 36.970 | >= 30% of GDP | MET | SGP gross capital formation mean = 36.970; threshold >= 30 |
| city_state_peer_check | 1.090 | >= 1.0x Hong Kong | MET | SGP/HKG GDP-pc 1990 = 1.090; threshold >= 1 |

## Interpretation
This is a pre-registered descriptive checklist over local vintages. It grades whether the observed Singapore pattern clears the stated thresholds; it does not identify a single causal lever inside the LKY-era bundle.

## Sources
- `world_bank_wdi:NY.GDP.PCAP.KD.ZG` -> `data/vintages/world_bank_wdi/NY.GDP.PCAP.KD.ZG@2026-04-30T140100Z.parquet`
- `world_bank_wdi:NY.GDP.PCAP.KD` -> `data/vintages/world_bank_wdi/NY.GDP.PCAP.KD@2026-04-30T135537Z.parquet`
- `world_bank_wdi:NE.GDI.TOTL.ZS` -> `data/vintages/world_bank_wdi/NE.GDI.TOTL.ZS@2026-04-30T135558Z.parquet`

## Steelman
See `hypotheses/steelman/singapore_lky_growth_takeoff_1965_1990.md`.
