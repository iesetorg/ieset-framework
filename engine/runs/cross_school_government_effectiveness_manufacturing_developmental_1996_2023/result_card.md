# Result card - cross_school_government_effectiveness_manufacturing_developmental_1996_2023

**Verdict:** PARTIAL - coefficient is not statistically decisive at p <= 0.10.

## Plain-English Claim

Government effectiveness predicts higher manufacturing value-added share.

## School Coverage

developmentalism, empirical_pragmatist

## What Was Measured

- Outcome: `manufacturing_share`.
- Treatment: `wgi_ge`.
- Controls: `gdp_pc_growth`.

## Results

- Usable panel: **4,386 observations**, **193 countries**.
- Coefficient on treatment: **-0.4019** (SE 0.4106, p=0.3276).

## Specification

`Q('manufacturing_share') ~ Q('wgi_ge') + Q('gdp_pc_growth') + C(country) + C(year)`

This is a cross-country panel screen with country and year fixed effects. Treat it as throughput evidence, not final causal proof.
