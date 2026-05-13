# Result card - eurostat_energy_price_services_vs_industry_reallocation

**Verdict:** PARTIAL - coefficient is not statistically decisive at p<0.10.

## Plain-English Claim

Higher industrial electricity prices accelerate reallocation from industry toward services.

## School Coverage

empirical_pragmatist, developmentalism, degrowth

## What Was Measured

- Outcome: `services_minus_industry_employment_share`.
- Treatment: `industrial_electricity_price`.
- Controls: `gdp_pc_growth`.

## Results

- Usable panel: **192 observations**, **33 countries**, 2019-2024.
- Coefficient on treatment: **1.3720** (SE 2.5756, p=0.5942).

## Specification

`Q('services_minus_industry_employment_share') ~ Q('industrial_electricity_price') + Q('gdp_pc_growth') + C(country) + C(year)`

This is a short European panel screen using local landed vintages. Treat it as throughput evidence, not final causal proof.
