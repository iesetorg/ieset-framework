# Result card - eurostat_energy_price_household_distribution_stress

**Verdict:** PARTIAL - coefficient is not statistically decisive at p<0.10

## Plain-English Claim

Energy-price spikes increase household distributional stress.

## What Was Measured

- Outcome: `distribution_stress`.
- Treatment: `household_electricity_price`.
- Controls: `gdp_pc_growth`.

## Results

- Usable panel: **170 observations**, **29 countries**, 2019-2024.
- Coefficient on treatment: **+2.674** (SE 7.6, p=0.725).

## Specification

`Q('distribution_stress') ~ Q('household_electricity_price') + Q('gdp_pc_growth') + C(country) + C(year)`

This is a short European household-energy panel screen using landed Eurostat and WDI vintages. Treat it as throughput evidence, not final causal proof.
