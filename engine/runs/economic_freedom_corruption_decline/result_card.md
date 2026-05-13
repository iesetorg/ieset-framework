# Result card - economic_freedom_corruption_decline

**Verdict:** SUPPORTED - V-Dem rule of law predicts lower political corruption (transformed beta=+0.393, p=0.000); 3/3 robustness outcomes have the same sign.

## What Was Measured

- Outcome: V-Dem political corruption, transformed so higher means less corruption.
- Treatment: V-Dem rule of law, where higher values mean stronger legal constraints.
- Control: log real GDP per capita from WDI.

## Primary Panel

| term | estimate | se | p | n obs | countries |
| --- | ---: | ---: | ---: | ---: | ---: |
| V-Dem rule of law | +0.393 | 0.100 | 0.000 | 1120 | 40 |

## Robustness Outcomes

| outcome | estimate | p | n obs |
| --- | ---: | ---: | ---: |
| public_sector_corruption | +0.283 | 0.025 | 1120 |
| executive_corruption | +0.602 | 0.000 | 1120 |
| clientelism | +0.230 | 0.045 | 1120 |

## Data

- vdem: `data/vintages/vdem/vdem_cy_full@2026-05-05T200021Z.parquet`
- gdp_pc: `data/vintages/world_bank_wdi/NY.GDP.PCAP.KD@2026-05-05T194645Z.parquet`
