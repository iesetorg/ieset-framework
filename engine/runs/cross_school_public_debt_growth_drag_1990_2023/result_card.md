# Result card - cross_school_public_debt_growth_drag_1990_2023

**Verdict:** REFUTED - coefficient is statistically significant in the opposite direction.

## Plain-English Claim

Public debt is not necessarily growth-damaging in broad panels.

## School Coverage

marxian, mmt, post_keynesian

## What Was Measured

- Outcome: `gdp_pc_growth`.
- Treatment: `public_debt`.
- Controls: none.

## Results

- Usable panel: **1,607 observations**, **109 countries**.
- Coefficient on treatment: **-0.0198** (SE 0.0053, p=0.0002).

## Specification

`Q('gdp_pc_growth') ~ Q('public_debt') + C(country) + C(year)`

This is a cross-country panel screen with country and year fixed effects. Treat it as throughput evidence, not final causal proof.
