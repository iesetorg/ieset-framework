# Result card - cross_school_energy_use_life_expectancy_degrowth_threshold_1990_2023

**Verdict:** PARTIAL - coefficient is not statistically decisive at p <= 0.10.

## Plain-English Claim

Higher energy use per capita predicts higher life expectancy.

## School Coverage

degrowth, eco_socialist

## What Was Measured

- Outcome: `life_expectancy`.
- Treatment: `energy_use_pc`.
- Controls: `gdp_pc_growth`.

## Results

- Usable panel: **5,012 observations**, **176 countries**.
- Coefficient on treatment: **0.0000** (SE 0.0001, p=0.7638).

## Specification

`Q('life_expectancy') ~ Q('energy_use_pc') + Q('gdp_pc_growth') + C(country) + C(year)`

This is a cross-country panel screen with country and year fixed effects. Treat it as throughput evidence, not final causal proof.
