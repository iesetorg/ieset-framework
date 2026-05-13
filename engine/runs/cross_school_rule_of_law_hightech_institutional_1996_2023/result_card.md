# Result card - cross_school_rule_of_law_hightech_institutional_1996_2023

**Verdict:** PARTIAL - coefficient is not statistically decisive at p <= 0.10.

## Plain-English Claim

Rule of law predicts higher high-tech export intensity.

## School Coverage

ordoliberal, classical_liberal

## What Was Measured

- Outcome: `high_tech_exports`.
- Treatment: `wgi_rl`.
- Controls: `gdp_pc_growth`.

## Results

- Usable panel: **2,514 observations**, **183 countries**.
- Coefficient on treatment: **0.7630** (SE 1.9527, p=0.6960).

## Specification

`Q('high_tech_exports') ~ Q('wgi_rl') + Q('gdp_pc_growth') + C(country) + C(year)`

This is a cross-country panel screen with country and year fixed effects. Treat it as throughput evidence, not final causal proof.
