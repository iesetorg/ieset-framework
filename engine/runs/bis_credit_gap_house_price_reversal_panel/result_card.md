# BIS credit gap predicts real house-price reversal

**Verdict:** supported — regression and raw high-vs-normal contrast both clear the predeclared gates.

## Predeclared Test

High credit-gap episode is BIS WS_CREDIT_GAP CG_DTYPE=C >= 10 percentage points; outcome is 12-quarter forward real residential property-price log growth from BIS WS_SPP VALUE=R index.

Decision gates: coefficient on `high_credit_gap` must be <= -3.0 with p <= 0.05; raw high-minus-normal mean difference must be <= -3.0; minimum coverage is 600 observations and 20 countries.

## Results

- Usable panel: **5,685 country-quarters**, **42 countries**.
- Clustered OLS coefficient on `high_credit_gap`: **-4.165** (SE 1.634, p=0.0108, 95% CI [-7.368, -0.961]).
- Raw high-minus-normal outcome mean: **-6.951** (-0.373 vs 6.578); high-stress/high-gap observations: **1,116**.

## Specification

`fwd_real_house_price_growth_12q ~ high_credit_gap + credit_gap + lag_real_house_price_growth_8q + C(country) + C(year)`

Country fixed effects and calendar-year fixed effects are included. Standard errors are clustered by BIS country code.

## Data

- BIS WS_CREDIT_GAP: credit gap CG_DTYPE=C and broad private credit/GDP CG_DTYPE=B.
- BIS WS_SPP: real residential property-price index, quarterly.
- BIS WS_DSR: household debt-service ratio, quarterly.
- BIS WS_EER: real broad effective exchange-rate index, monthly aggregated to quarterly means.

## Caveats

This is a compact panel screen, not a causal design. The fixed-effects controls remove persistent country differences and common annual shocks, but not time-varying local policy, banking regulation, migration, construction constraints, or terms-of-trade shocks. The test is therefore a falsifiable predictive verdict for the predeclared BIS signal rather than a structural causal estimate.
