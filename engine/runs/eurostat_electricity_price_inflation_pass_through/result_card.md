# Result card - eurostat_electricity_price_inflation_pass_through

**Verdict:** SUPPORTED - coefficient is statistically significant in the predicted direction.

## Plain-English Claim

Industrial electricity-price inflation passes through to headline CPI inflation.

## School Coverage

new_keynesian, post_keynesian, chicago_monetarism

## What Was Measured

- Outcome: `cpi_inflation`.
- Treatment: `electricity_price_yoy`.
- Controls: none.

## Results

- Usable panel: **226 observations**, **39 countries**, 2019-2024.
- Coefficient on treatment: **0.0261** (SE 0.0121, p=0.0307).

## Specification

`Q('cpi_inflation') ~ Q('electricity_price_yoy') + C(country) + C(year)`

This is a short European panel screen using local landed vintages. Treat it as throughput evidence, not final causal proof.
