# Result card - cross_school_gini_employment_underconsumption_1990_2023

**Verdict:** PARTIAL - coefficient is not statistically decisive at p <= 0.10.

## Plain-English Claim

Higher inequality predicts weaker employment outcomes.

## School Coverage

marxian, social_democratic

## What Was Measured

- Outcome: `employment`.
- Treatment: `gini`.
- Controls: `gdp_pc_growth`.

## Results

- Usable panel: **2,154 observations**, **163 countries**.
- Coefficient on treatment: **-0.0074** (SE 0.0614, p=0.9040).

## Specification

`Q('employment') ~ Q('gini') + Q('gdp_pc_growth') + C(country) + C(year)`

This is a cross-country panel screen with country and year fixed effects. Treat it as throughput evidence, not final causal proof.
