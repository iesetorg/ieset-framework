# Result card - cross_school_energy_use_growth_degrowth_tradeoff_1990_2023

**Verdict:** REFUTED - coefficient is statistically significant in the opposite direction.

## Plain-English Claim

Higher energy use per capita predicts faster GDP growth.

## School Coverage

degrowth, eco_socialist

## What Was Measured

- Outcome: `gdp_pc_growth`.
- Treatment: `energy_use_pc`.
- Controls: none.

## Results

- Usable panel: **5,012 observations**, **176 countries**.
- Coefficient on treatment: **-0.0006** (SE 0.0002, p=0.0089).

## Specification

`Q('gdp_pc_growth') ~ Q('energy_use_pc') + C(country) + C(year)`

This is a cross-country panel screen with country and year fixed effects. Treat it as throughput evidence, not final causal proof.
