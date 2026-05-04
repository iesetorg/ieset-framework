# Result card - singapore_lky_low_tax_high_savings_market_rules_1970_1990

**Verdict:** SUPPORTED - 5 of 5 metrics met threshold (support threshold 4)

## Pre-registration
- **Claim:** The LKY-era Singapore fiscal-market model combined high national savings, relatively low tax take, fiscal surpluses, and high economic/trade-freedom scores rather than relying on a large transfer state.
- **Falsification rule:** SUPPORTED if at least 4 of 5 metrics meet their thresholds; REFUTED if at most 2 meet after available data are evaluated.
- **Falsification test:** singapore_lky_low_tax_high_savings_market_rules_1970_1990_local_multimetric_checklist

## Metric Results
| metric | observed | threshold | status | note |
|---|---:|---|---|---|
| gross_savings_high | 35.525 | >= 30% of GNI | MET | SGP gross savings mean = 35.525; threshold >= 30 |
| tax_take_low | 15.877 | <= 18% of GDP | MET | SGP tax revenue/GDP mean = 15.877; threshold <= 18 |
| net_lending_surplus | 6.057 | >= 3% of GDP | MET | SGP net lending/GDP mean = 6.057; threshold >= 3 |
| economic_freedom_1990 | 8.721 | >= 8.0 | MET | SGP EFW summary 1990 = 8.721; threshold >= 8 |
| trade_freedom_1990 | 10.000 | >= 9.0 | MET | SGP EFW trade freedom 1990 = 10.000; threshold >= 9 |

## Interpretation
This is a pre-registered descriptive checklist over local vintages. It grades whether the observed Singapore pattern clears the stated thresholds; it does not identify a single causal lever inside the LKY-era bundle.

## Sources
- `world_bank_wdi:NY.GNS.ICTR.ZS` -> `data/vintages/world_bank_wdi/NY.GNS.ICTR.ZS@2026-04-30T114720Z.parquet`
- `world_bank_wdi:GC.TAX.TOTL.GD.ZS` -> `data/vintages/world_bank_wdi/GC.TAX.TOTL.GD.ZS@2026-04-30T114943Z.parquet`
- `world_bank_wdi:GC.NLD.TOTL.GD.ZS` -> `data/vintages/world_bank_wdi/GC.NLD.TOTL.GD.ZS@2026-04-30T140120Z.parquet`
- `fraser_efw:summary_index` -> `data/vintages/fraser_efw/summary_index@2026-05-02T220000Z.parquet`
- `fraser_efw:freedom_to_trade_internationally` -> `data/vintages/fraser_efw/freedom_to_trade_internationally@2026-05-02T220000Z.parquet`

## Steelman
See `hypotheses/steelman/singapore_lky_low_tax_high_savings_market_rules_1970_1990.md`.
