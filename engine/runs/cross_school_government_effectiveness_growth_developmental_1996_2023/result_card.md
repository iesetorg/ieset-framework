# Result card - cross_school_government_effectiveness_growth_developmental_1996_2023

**Verdict:** PARTIAL - coefficient is not statistically decisive at p <= 0.10.

## Plain-English Claim

Government effectiveness predicts faster GDP per-capita growth.

## School Coverage

developmentalism, ordoliberal

## What Was Measured

- Outcome: `gdp_pc_growth`.
- Treatment: `wgi_ge`.
- Controls: none.

## Results

- Usable panel: **4,866 observations**, **204 countries**.
- Coefficient on treatment: **0.2799** (SE 0.4077, p=0.4923).

## Specification

`Q('gdp_pc_growth') ~ Q('wgi_ge') + C(country) + C(year)`

This is a cross-country panel screen with country and year fixed effects. Treat it as throughput evidence, not final causal proof.
