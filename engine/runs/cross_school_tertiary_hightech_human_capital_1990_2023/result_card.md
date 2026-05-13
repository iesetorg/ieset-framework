# Result card - cross_school_tertiary_hightech_human_capital_1990_2023

**Verdict:** PARTIAL - coefficient is not statistically decisive at p <= 0.10.

## Plain-English Claim

Tertiary enrollment predicts higher high-tech export intensity.

## School Coverage

developmentalism, social_democratic

## What Was Measured

- Outcome: `high_tech_exports`.
- Treatment: `tertiary`.
- Controls: `gdp_pc_growth`.

## Results

- Usable panel: **1,855 observations**, **165 countries**.
- Coefficient on treatment: **0.0281** (SE 0.0528, p=0.5944).

## Specification

`Q('high_tech_exports') ~ Q('tertiary') + Q('gdp_pc_growth') + C(country) + C(year)`

This is a cross-country panel screen with country and year fixed effects. Treat it as throughput evidence, not final causal proof.
