# Result card - cross_school_fossil_electricity_life_expectancy_tradeoff_1990_2023

**Verdict:** REFUTED - coefficient is statistically significant in the opposite direction.

## Plain-English Claim

Higher fossil-electricity shares predict lower life expectancy after controls.

## School Coverage

eco_socialist, degrowth

## What Was Measured

- Outcome: `life_expectancy`.
- Treatment: `fossil_electricity`.
- Controls: `gdp_pc_growth`.

## Results

- Usable panel: **5,945 observations**, **206 countries**.
- Coefficient on treatment: **0.0185** (SE 0.0075, p=0.0136).

## Specification

`Q('life_expectancy') ~ Q('fossil_electricity') + Q('gdp_pc_growth') + C(country) + C(year)`

This is a cross-country panel screen with country and year fixed effects. Treat it as throughput evidence, not final causal proof.
