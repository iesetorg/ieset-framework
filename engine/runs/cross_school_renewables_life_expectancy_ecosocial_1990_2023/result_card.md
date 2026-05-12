# Result card - cross_school_renewables_life_expectancy_ecosocial_1990_2023

**Verdict:** REFUTED - coefficient is statistically significant in the opposite direction.

## Plain-English Claim

Higher renewable-electricity shares predict higher life expectancy.

## School Coverage

eco_socialist, degrowth

## What Was Measured

- Outcome: `life_expectancy`.
- Treatment: `renewable_electricity`.
- Controls: `gdp_pc_growth`.

## Results

- Usable panel: **5,584 observations**, **206 countries**.
- Coefficient on treatment: **-0.0153** (SE 0.0070, p=0.0289).

## Specification

`Q('life_expectancy') ~ Q('renewable_electricity') + Q('gdp_pc_growth') + C(country) + C(year)`

This is a cross-country panel screen with country and year fixed effects. Treat it as throughput evidence, not final causal proof.
