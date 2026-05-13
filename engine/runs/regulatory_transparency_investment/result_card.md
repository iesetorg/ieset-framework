# Result card - regulatory_transparency_investment

**Verdict:** PARTIAL - direct PMR estimate is not strong enough for support/refutation (panel beta=+0.407, p=0.656; change beta=+0.577).

## What Was Measured

- Outcome: investment share, measured as gross capital formation as a percent of GDP.
- Treatment: OECD PMR regulatory-process burden, averaging regulations impact evaluation, administrative burden, impact assessment, and stakeholder engagement scores.
- Interpretation: higher PMR scores mean more restrictive or weaker regulatory process quality, so a negative coefficient supports the claim.

## Primary Panel

| term | estimate | se | p | n obs | countries |
| --- | ---: | ---: | ---: | ---: | ---: |
| PMR process burden | +0.407 | 0.906 | 0.656 | 104 | 54 |

## 2018-2023 Change Check

| term | estimate | se | p approx | n countries |
| --- | ---: | ---: | ---: | ---: |
| 2018 PMR process burden | +0.577 | 0.413 | 0.163 | 50 |

## Data

- oecd_pmr: `data/vintages/oecd_pmr/PMR@2026-05-05T200616Z.parquet`
- investment_share: `data/vintages/world_bank_wdi/NE.GDI.TOTL.ZS@2026-05-05T194659Z.parquet`
- gdp_pc: `data/vintages/world_bank_wdi/NY.GDP.PCAP.KD@2026-05-05T194645Z.parquet`
- trade_openness: `data/vintages/world_bank_wdi/NE.TRD.GNFS.ZS@2026-05-05T194657Z.parquet`
