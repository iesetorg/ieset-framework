# Result card - uae_dubai_tourism_aviation_hub_2015_2019

**Verdict:** SUPPORTED - 4 of 4 metrics met threshold (support threshold 3)

## Pre-registration
- **Claim:** Dubai/UAE aviation, airport, and tourism policy achieved exceptional pre-COVID visitor-hub scale by Gulf standards, visible in absolute arrivals, arrivals per resident, and arrivals relative to GCC peers.
- **Falsification rule:** SUPPORTED if at least 3 of 4 metrics meet their thresholds; REFUTED if at most 1 meet after available data are evaluated.
- **Falsification test:** uae_dubai_tourism_aviation_hub_2015_2019_local_multimetric_checklist

## Metric Results
| metric | observed | threshold | status | note |
|---|---:|---|---|---|
| visitor_arrivals_2019 | 25282000.000 | >= 20 million | MET | ARE tourist arrivals 2019 = 25282000.000; threshold >= 2e+07 |
| visitor_arrivals_per_capita_2019 | 2.677 | >= 2.0 arrivals per resident | MET | ARE visitor arrivals per resident 2019 = 2.677; threshold >= 2 |
| visitor_arrivals_vs_gcc_2019 | 2.952 | >= 2.0x peer median | MET | ARE arrivals / GCC median 2019 = 2.952; threshold >= 2 |
| trade_openness_context_2019 | 163.822 | >= 150% of GDP | MET | ARE trade/GDP 2019 = 163.822; threshold >= 150 |

## Interpretation
This is a pre-registered descriptive checklist over local vintages. It grades whether the observed case pattern clears the stated thresholds; it does not identify a single causal lever inside the policy bundle.

## Sources
- `world_bank_wdi:ST.INT.ARVL` -> `data/vintages/world_bank_wdi/ST.INT.ARVL@2026-04-30T130312Z.parquet`
- `world_bank_wdi:SP.POP.TOTL` -> `data/vintages/world_bank_wdi/SP.POP.TOTL@2026-04-30T135559Z.parquet`
- `world_bank_wdi:NE.TRD.GNFS.ZS` -> `data/vintages/world_bank_wdi/NE.TRD.GNFS.ZS@2026-04-30T135618Z.parquet`

## Steelman
See `hypotheses/steelman/uae_dubai_tourism_aviation_hub_2015_2019.md`.
