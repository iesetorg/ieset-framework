# Result card - cross_school_renewables_child_mortality_ecosocial_1990_2023

**Verdict:** REFUTED - coefficient is statistically significant in the opposite direction.

## Plain-English Claim

Higher renewable-electricity shares predict lower child mortality.

## School Coverage

eco_socialist, degrowth

## What Was Measured

- Outcome: `child_mortality`.
- Treatment: `renewable_electricity`.
- Controls: `gdp_pc_growth`.

## Results

- Usable panel: **5,336 observations**, **192 countries**.
- Coefficient on treatment: **0.2580** (SE 0.0758, p=0.0007).

## Specification

`Q('child_mortality') ~ Q('renewable_electricity') + Q('gdp_pc_growth') + C(country) + C(year)`

This is a cross-country panel screen with country and year fixed effects. Treat it as throughput evidence, not final causal proof.
