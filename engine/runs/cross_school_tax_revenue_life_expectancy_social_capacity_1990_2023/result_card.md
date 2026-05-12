# Result card - cross_school_tax_revenue_life_expectancy_social_capacity_1990_2023

**Verdict:** REFUTED - coefficient is statistically significant in the opposite direction.

## Plain-English Claim

Higher tax revenue shares predict higher life expectancy through public capacity.

## School Coverage

social_democratic, new_keynesian

## What Was Measured

- Outcome: `life_expectancy`.
- Treatment: `tax_revenue`.
- Controls: `gdp_pc_growth`.

## Results

- Usable panel: **3,781 observations**, **159 countries**.
- Coefficient on treatment: **-0.0024** (SE 0.0014, p=0.0743).

## Specification

`Q('life_expectancy') ~ Q('tax_revenue') + Q('gdp_pc_growth') + C(country) + C(year)`

This is a cross-country panel screen with country and year fixed effects. Treat it as throughput evidence, not final causal proof.
