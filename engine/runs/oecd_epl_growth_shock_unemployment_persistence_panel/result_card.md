# Result card - oecd_epl_growth_shock_unemployment_persistence_panel

**Verdict:** REFUTED - neither the regression nor raw high-low contrast gate clears.

## Plain-English Claim

Negative growth shocks translate into more persistent unemployment where employment protection is stricter.

## Results

- Usable panel: **1,482 observations**, **37 country units**.
- Treatment: `high_epl_x_negative_growth`.
- Outcome: `fwd_unemployment_change_2y`.
- Coefficient: **-0.4363** (clustered SE 0.5160, p=0.3978).
- Top-quartile raw contrast: **nan**.

## Specification

`fwd_unemployment_change_2y ~ high_epl_x_negative_growth + epl + negative_growth + unemployment_rate + C(country) + C(year)`

This is a fixed-effects readiness screen using local vintages. It is not a standalone causal estimate.
