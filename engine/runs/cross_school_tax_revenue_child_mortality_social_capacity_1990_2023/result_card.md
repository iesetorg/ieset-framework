# Result card - cross_school_tax_revenue_child_mortality_social_capacity_1990_2023

**Verdict:** REFUTED - coefficient is statistically significant in the opposite direction.

## Plain-English Claim

Higher tax revenue shares predict lower child mortality.

## School Coverage

social_democratic, new_keynesian

## What Was Measured

- Outcome: `child_mortality`.
- Treatment: `tax_revenue`.
- Controls: `gdp_pc_growth`.

## Results

- Usable panel: **3,753 observations**, **158 countries**.
- Coefficient on treatment: **0.0564** (SE 0.0140, p=0.0001).

## Specification

`Q('child_mortality') ~ Q('tax_revenue') + Q('gdp_pc_growth') + C(country) + C(year)`

This is a cross-country panel screen with country and year fixed effects. Treat it as throughput evidence, not final causal proof.
