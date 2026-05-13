# Result card - cross_school_government_effectiveness_fdi_developmental_1996_2023

**Verdict:** PARTIAL - coefficient is not statistically decisive at p <= 0.10.

## Plain-English Claim

Government effectiveness predicts higher FDI inflows.

## School Coverage

developmentalism, ordoliberal

## What Was Measured

- Outcome: `fdi`.
- Treatment: `wgi_ge`.
- Controls: `gdp_pc_growth`.

## Results

- Usable panel: **4,638 observations**, **197 countries**.
- Coefficient on treatment: **1.6926** (SE 1.6293, p=0.2989).

## Specification

`Q('fdi') ~ Q('wgi_ge') + Q('gdp_pc_growth') + C(country) + C(year)`

This is a cross-country panel screen with country and year fixed effects. Treat it as throughput evidence, not final causal proof.
