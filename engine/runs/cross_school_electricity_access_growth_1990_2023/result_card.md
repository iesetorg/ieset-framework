# Result card - cross_school_electricity_access_growth_1990_2023

**Verdict:** PARTIAL - coefficient is not statistically decisive at p <= 0.10.

## Plain-English Claim

Electricity access predicts faster GDP per-capita growth.

## School Coverage

developmentalism, classical_liberal

## What Was Measured

- Outcome: `gdp_pc_growth`.
- Treatment: `electricity_access`.
- Controls: none.

## Results

- Usable panel: **6,137 observations**, **211 countries**.
- Coefficient on treatment: **-0.0108** (SE 0.0145, p=0.4553).

## Specification

`Q('gdp_pc_growth') ~ Q('electricity_access') + C(country) + C(year)`

This is a cross-country panel screen with country and year fixed effects. Treat it as throughput evidence, not final causal proof.
