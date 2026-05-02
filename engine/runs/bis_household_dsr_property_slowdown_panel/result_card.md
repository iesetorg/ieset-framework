# Household debt-service stress predicts property slowdown

**Verdict:** partial — one of the regression or raw-contrast gates clears, but not both.

## Predeclared Test

High household-DSR stress is BIS WS_DSR DSR_BORROWERS=H above 12 percent and above the country's own predeclared 75th percentile; outcome is 8-quarter forward real residential property-price log growth from WS_SPP VALUE=R index.

Decision gates: coefficient on `high_household_dsr` must be <= -2.0 with p <= 0.05; raw high-minus-normal mean difference must be <= -2.0; minimum coverage is 400 observations and 15 countries.

## Results

- Usable panel: **1,698 country-quarters**, **17 countries**.
- Clustered OLS coefficient on `high_household_dsr`: **0.715** (SE 1.896, p=0.7060, 95% CI [-3.001, 4.432]).
- Raw high-minus-normal outcome mean: **-7.419** (-3.056 vs 4.363); high-stress/high-gap observations: **158**.

## Specification

`fwd_real_house_price_growth_8q ~ high_household_dsr + household_dsr + lag_real_house_price_growth_8q + C(country) + C(year)`

Country fixed effects and calendar-year fixed effects are included. Standard errors are clustered by BIS country code.

## Data

- BIS WS_CREDIT_GAP: credit gap CG_DTYPE=C and broad private credit/GDP CG_DTYPE=B.
- BIS WS_SPP: real residential property-price index, quarterly.
- BIS WS_DSR: household debt-service ratio, quarterly.
- BIS WS_EER: real broad effective exchange-rate index, monthly aggregated to quarterly means.

## Caveats

This is a compact panel screen, not a causal design. The fixed-effects controls remove persistent country differences and common annual shocks, but not time-varying local policy, banking regulation, migration, construction constraints, or terms-of-trade shocks. The test is therefore a falsifiable predictive verdict for the predeclared BIS signal rather than a structural causal estimate.
