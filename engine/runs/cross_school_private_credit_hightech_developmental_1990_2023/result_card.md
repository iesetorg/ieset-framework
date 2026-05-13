# Result card - cross_school_private_credit_hightech_developmental_1990_2023

**Verdict:** PARTIAL - coefficient is not statistically decisive at p <= 0.10.

## Plain-English Claim

Private credit depth predicts higher high-tech export intensity.

## School Coverage

developmentalism, post_keynesian

## What Was Measured

- Outcome: `high_tech_exports`.
- Treatment: `private_credit`.
- Controls: `gdp_pc_growth`.

## Results

- Usable panel: **2,206 observations**, **175 countries**.
- Coefficient on treatment: **0.0358** (SE 0.0227, p=0.1142).

## Specification

`Q('high_tech_exports') ~ Q('private_credit') + Q('gdp_pc_growth') + C(country) + C(year)`

This is a cross-country panel screen with country and year fixed effects. Treat it as throughput evidence, not final causal proof.
