# Real exchange-rate appreciation mean-reverts

**Verdict:** refuted — neither the regression nor raw-contrast gate clears.

## Predeclared Test

Large appreciation is 12-quarter log change in the BIS WS_EER monthly real broad effective exchange-rate index >= 15 percent; outcome is 8-quarter forward REER log change.

Decision gates: coefficient on `large_reer_appreciation` must be <= -2.0 with p <= 0.05; raw high-minus-normal mean difference must be <= -2.0; minimum coverage is 1200 observations and 25 countries.

## Results

- Usable panel: **6,976 country-quarters**, **64 countries**.
- Clustered OLS coefficient on `large_reer_appreciation`: **2.319** (SE 1.388, p=0.0947, 95% CI [-0.401, 5.039]).
- Raw high-minus-normal outcome mean: **-1.771** (-1.400 vs 0.371); high-stress/high-gap observations: **564**.

## Specification

`fwd_reer_growth_8q ~ large_reer_appreciation + reer_appreciation_12q + C(country) + C(year)`

Country fixed effects and calendar-year fixed effects are included. Standard errors are clustered by BIS country code.

## Data

- BIS WS_CREDIT_GAP: credit gap CG_DTYPE=C and broad private credit/GDP CG_DTYPE=B.
- BIS WS_SPP: real residential property-price index, quarterly.
- BIS WS_DSR: household debt-service ratio, quarterly.
- BIS WS_EER: real broad effective exchange-rate index, monthly aggregated to quarterly means.

## Caveats

This is a compact panel screen, not a causal design. The fixed-effects controls remove persistent country differences and common annual shocks, but not time-varying local policy, banking regulation, migration, construction constraints, or terms-of-trade shocks. The test is therefore a falsifiable predictive verdict for the predeclared BIS signal rather than a structural causal estimate.
