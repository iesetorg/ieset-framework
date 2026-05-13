# Result card - cross_school_smaller_government_growth_1990_2023

**Verdict:** PARTIAL - coefficient is not statistically decisive at p <= 0.10.

## Plain-English Claim

Smaller-government EFW scores predict faster GDP per-capita growth.

## School Coverage

austrian, classical_liberal, chicago_monetarism

## What Was Measured

- Outcome: `gdp_pc_growth`.
- Treatment: `efw_size_government`.
- Controls: none.

## Results

- Usable panel: **4,159 observations**, **164 countries**.
- Coefficient on treatment: **-0.1713** (SE 0.1710, p=0.3164).

## Specification

`Q('gdp_pc_growth') ~ Q('efw_size_government') + C(country) + C(year)`

This is a cross-country panel screen with country and year fixed effects. Treat it as throughput evidence, not final causal proof.
