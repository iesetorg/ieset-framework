# Result card - eurostat_household_electricity_price_consumption_panel

**Verdict:** PARTIAL - coefficient is not statistically decisive at p<0.10

## Plain-English Claim

Higher household electricity prices reduce real household consumption growth.

## What Was Measured

- Outcome: `household_consumption_growth`.
- Treatment: `household_electricity_price`.
- Controls: `gdp_pc_growth`.

## Results

- Usable panel: **151 observations**, **29 countries**, 2019-2024.
- Coefficient on treatment: **-5.28** (SE 9.811, p=0.5904).

## Specification

`Q('household_consumption_growth') ~ Q('household_electricity_price') + Q('gdp_pc_growth') + C(country) + C(year)`

This is a short European household-energy panel screen using landed Eurostat and WDI vintages. Treat it as throughput evidence, not final causal proof.
