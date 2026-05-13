# Result card - eurostat_electricity_price_volatility_industrial_exit

**Verdict:** PARTIAL - coefficient is not statistically decisive at p<0.10.

## Plain-English Claim

Industrial electricity-price volatility predicts industrial employment-share decline.

## School Coverage

austrian, ordoliberal, developmentalism

## What Was Measured

- Outcome: `industry_employment_share`.
- Treatment: `electricity_price_volatility`.
- Controls: `gdp_pc_growth`.

## Results

- Usable panel: **192 observations**, **33 countries**, 2019-2024.
- Coefficient on treatment: **0.0055** (SE 0.0045, p=0.2269).

## Specification

`Q('industry_employment_share') ~ Q('electricity_price_volatility') + Q('gdp_pc_growth') + C(country) + C(year)`

This is a short European panel screen using local landed vintages. Treat it as throughput evidence, not final causal proof.
