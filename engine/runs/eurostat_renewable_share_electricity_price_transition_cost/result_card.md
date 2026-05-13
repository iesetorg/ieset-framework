# Result card - eurostat_renewable_share_electricity_price_transition_cost

**Verdict:** PARTIAL - coefficient is not statistically decisive at p<0.10.

## Plain-English Claim

Higher renewable-electricity shares are associated with higher industrial prices during the transition window.

## School Coverage

eco_socialist, degrowth, classical_liberal

## What Was Measured

- Outcome: `industrial_electricity_price`.
- Treatment: `renewable_share`.
- Controls: `gdp_pc_growth`.

## Results

- Usable panel: **227 observations**, **39 countries**, 2019-2024.
- Coefficient on treatment: **0.0007** (SE 0.0007, p=0.3567).

## Specification

`Q('industrial_electricity_price') ~ Q('renewable_share') + Q('gdp_pc_growth') + C(country) + C(year)`

This is a short European panel screen using local landed vintages. Treat it as throughput evidence, not final causal proof.
