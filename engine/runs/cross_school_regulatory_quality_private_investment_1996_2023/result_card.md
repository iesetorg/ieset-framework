# Result card - cross_school_regulatory_quality_private_investment_1996_2023

**Verdict:** SUPPORTED - coefficient has the predeclared sign and p <= 0.10.

## Plain-English Claim

Regulatory quality predicts higher private-investment shares.

## School Coverage

ordoliberal, empirical_pragmatist

## What Was Measured

- Outcome: `private_investment`.
- Treatment: `wgi_rq`.
- Controls: `gdp_pc_growth`.

## Results

- Usable panel: **1,652 observations**, **97 countries**.
- Coefficient on treatment: **2.3150** (SE 1.0289, p=0.0245).

## Specification

`Q('private_investment') ~ Q('wgi_rq') + Q('gdp_pc_growth') + C(country) + C(year)`

This is a cross-country panel screen with country and year fixed effects. Treat it as throughput evidence, not final causal proof.
