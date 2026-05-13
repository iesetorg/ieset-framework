# Result card - cross_school_government_effectiveness_hightech_developmental_1996_2023

**Verdict:** PARTIAL - coefficient is not statistically decisive at p <= 0.10.

## Plain-English Claim

Government effectiveness predicts higher high-tech export intensity.

## School Coverage

developmentalism, ordoliberal, empirical_pragmatist

## What Was Measured

- Outcome: `high_tech_exports`.
- Treatment: `wgi_ge`.
- Controls: `gdp_pc_growth`.

## Results

- Usable panel: **2,509 observations**, **182 countries**.
- Coefficient on treatment: **0.8423** (SE 1.0348, p=0.4157).

## Specification

`Q('high_tech_exports') ~ Q('wgi_ge') + Q('gdp_pc_growth') + C(country) + C(year)`

This is a cross-country panel screen with country and year fixed effects. Treat it as throughput evidence, not final causal proof.
