# Result card - cross_school_fdi_hightech_developmental_1990_2023

**Verdict:** PARTIAL - coefficient is not statistically decisive at p <= 0.10.

## Plain-English Claim

FDI inflows predict higher high-tech export intensity.

## School Coverage

developmentalism, empirical_pragmatist

## What Was Measured

- Outcome: `high_tech_exports`.
- Treatment: `fdi`.
- Controls: `gdp_pc_growth`.

## Results

- Usable panel: **2,494 observations**, **180 countries**.
- Coefficient on treatment: **0.0008** (SE 0.0034, p=0.8217).

## Specification

`Q('high_tech_exports') ~ Q('fdi') + Q('gdp_pc_growth') + C(country) + C(year)`

This is a cross-country panel screen with country and year fixed effects. Treat it as throughput evidence, not final causal proof.
