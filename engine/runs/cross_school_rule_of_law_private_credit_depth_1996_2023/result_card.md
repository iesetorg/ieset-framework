# Result card - cross_school_rule_of_law_private_credit_depth_1996_2023

**Verdict:** SUPPORTED - coefficient has the predeclared sign and p <= 0.10.

## Plain-English Claim

Rule of law predicts deeper private credit intermediation.

## School Coverage

ordoliberal, classical_liberal

## What Was Measured

- Outcome: `private_credit`.
- Treatment: `wgi_rl`.
- Controls: `gdp_pc_growth`.

## Results

- Usable panel: **3,872 observations**, **186 countries**.
- Coefficient on treatment: **6.8877** (SE 2.6623, p=0.0097).

## Specification

`Q('private_credit') ~ Q('wgi_rl') + Q('gdp_pc_growth') + C(country) + C(year)`

This is a cross-country panel screen with country and year fixed effects. Treat it as throughput evidence, not final causal proof.
