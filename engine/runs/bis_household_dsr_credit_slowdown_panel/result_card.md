# Household debt-service stress predicts credit slowdown

**Verdict:** refuted — neither the regression nor raw-contrast gate clears.

## Predeclared Test

High household-DSR stress is BIS WS_DSR DSR_BORROWERS=H above 12 percent and above the country's own predeclared 75th percentile; outcome is 8-quarter forward change in broad private credit/GDP from WS_CREDIT_GAP CG_DTYPE=B.

Decision gates: coefficient on `high_household_dsr` must be <= -2.0 with p <= 0.05; raw high-minus-normal mean difference must be <= -2.0; minimum coverage is 500 observations and 15 countries.

## Results

- Usable panel: **1,683 country-quarters**, **17 countries**.
- Clustered OLS coefficient on `high_household_dsr`: **2.035** (SE 2.015, p=0.3126, 95% CI [-1.914, 5.983]).
- Raw high-minus-normal outcome mean: **7.433** (11.598 vs 4.165); high-stress/high-gap observations: **153**.

## Specification

`fwd_credit_growth_8q ~ high_household_dsr + household_dsr + lag_credit_growth_8q + C(country) + C(year)`

Country fixed effects and calendar-year fixed effects are included. Standard errors are clustered by BIS country code.

## Data

- BIS WS_CREDIT_GAP: credit gap CG_DTYPE=C and broad private credit/GDP CG_DTYPE=B.
- BIS WS_SPP: real residential property-price index, quarterly.
- BIS WS_DSR: household debt-service ratio, quarterly.
- BIS WS_EER: real broad effective exchange-rate index, monthly aggregated to quarterly means.

## Caveats

This is a compact panel screen, not a causal design. The fixed-effects controls remove persistent country differences and common annual shocks, but not time-varying local policy, banking regulation, migration, construction constraints, or terms-of-trade shocks. The test is therefore a falsifiable predictive verdict for the predeclared BIS signal rather than a structural causal estimate.
