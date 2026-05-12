# Result card - cross_school_fossil_electricity_child_mortality_ecosocial_1990_2023

**Verdict:** REFUTED - coefficient is statistically significant in the opposite direction.

## Plain-English Claim

Higher fossil-electricity shares predict worse child-mortality outcomes.

## School Coverage

eco_socialist, degrowth

## What Was Measured

- Outcome: `child_mortality`.
- Treatment: `fossil_electricity`.
- Controls: `gdp_pc_growth`.

## Results

- Usable panel: **5,695 observations**, **192 countries**.
- Coefficient on treatment: **-0.2384** (SE 0.0774, p=0.0021).

## Specification

`Q('child_mortality') ~ Q('fossil_electricity') + Q('gdp_pc_growth') + C(country) + C(year)`

This is a cross-country panel screen with country and year fixed effects. Treat it as throughput evidence, not final causal proof.
