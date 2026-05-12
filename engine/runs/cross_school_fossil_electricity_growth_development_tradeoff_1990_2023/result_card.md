# Result card - cross_school_fossil_electricity_growth_development_tradeoff_1990_2023

**Verdict:** REFUTED - coefficient is statistically significant in the opposite direction.

## Plain-English Claim

Higher fossil-electricity shares predict faster GDP growth in development panels.

## School Coverage

eco_socialist, developmentalism

## What Was Measured

- Outcome: `gdp_pc_growth`.
- Treatment: `fossil_electricity`.
- Controls: none.

## Results

- Usable panel: **5,945 observations**, **206 countries**.
- Coefficient on treatment: **-0.0328** (SE 0.0124, p=0.0080).

## Specification

`Q('gdp_pc_growth') ~ Q('fossil_electricity') + C(country) + C(year)`

This is a cross-country panel screen with country and year fixed effects. Treat it as throughput evidence, not final causal proof.
