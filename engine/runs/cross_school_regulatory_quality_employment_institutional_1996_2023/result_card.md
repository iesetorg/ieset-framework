# Result card - cross_school_regulatory_quality_employment_institutional_1996_2023

**Verdict:** PARTIAL - coefficient is not statistically decisive at p <= 0.10.

## Plain-English Claim

Regulatory quality predicts higher employment.

## School Coverage

ordoliberal, empirical_pragmatist

## What Was Measured

- Outcome: `employment`.
- Treatment: `wgi_rq`.
- Controls: `gdp_pc_growth`.

## Results

- Usable panel: **4,468 observations**, **183 countries**.
- Coefficient on treatment: **0.4736** (SE 0.5705, p=0.4065).

## Specification

`Q('employment') ~ Q('wgi_rq') + Q('gdp_pc_growth') + C(country) + C(year)`

This is a cross-country panel screen with country and year fixed effects. Treat it as throughput evidence, not final causal proof.
