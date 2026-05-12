# Result card - cross_school_electricity_access_child_mortality_1990_2023

**Verdict:** SUPPORTED - coefficient has the predeclared sign and p <= 0.10.

## Plain-English Claim

Electricity access predicts lower child mortality.

## School Coverage

developmentalism, eco_socialist

## What Was Measured

- Outcome: `child_mortality`.
- Treatment: `electricity_access`.
- Controls: `gdp_pc_growth`.

## Results

- Usable panel: **5,693 observations**, **193 countries**.
- Coefficient on treatment: **-0.8886** (SE 0.0931, p=0.0000).

## Specification

`Q('child_mortality') ~ Q('electricity_access') + Q('gdp_pc_growth') + C(country) + C(year)`

This is a cross-country panel screen with country and year fixed effects. Treat it as throughput evidence, not final causal proof.
