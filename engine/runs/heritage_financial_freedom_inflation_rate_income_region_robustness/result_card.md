# Result card — heritage_financial_freedom_inflation_rate_income_region_robustness

**Verdict:** PARTIAL — controlled coefficient not decisive (coef=-3.736, p=0.1035)

## Design
- Heritage component: `financial_freedom` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:FP.CPI.TOTL.ZG` latest available country observation since `2018`.

## Estimate
- High-market mean: `7.032107508210012` over `64` countries.
- Low-market mean: `11.524997514199452` over `65` countries.
- Difference, high minus low: `-4.49289000598944`.
- Welch p-value: `0.3151422183100049`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `167`.
- Market-score coefficient, standardized score: `-3.7361620990375037`.
- Controlled p-value: `0.10345982155598392`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
