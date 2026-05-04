# Result card — heritage_government_spending_inflation_rate_income_region_robustness

**Verdict:** PARTIAL — controlled coefficient not decisive (coef=2.042, p=0.3468)

## Design
- Heritage component: `government_spending` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:FP.CPI.TOTL.ZG` latest available country observation since `2018`.

## Estimate
- High-market mean: `14.273211759796178` over `42` countries.
- Low-market mean: `3.08226655900758` over `42` countries.
- Difference, high minus low: `11.190945200788597`.
- Welch p-value: `0.009955570531153599`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `167`.
- Market-score coefficient, standardized score: `2.042204732359126`.
- Controlled p-value: `0.3467681867208472`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
