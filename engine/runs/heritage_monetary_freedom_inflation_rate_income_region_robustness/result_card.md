# Result card — heritage_monetary_freedom_inflation_rate_income_region_robustness

**Verdict:** SUPPORTED — controlled market-score coefficient has expected sign - and p=1.12e-29

## Design
- Heritage component: `monetary_freedom` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:FP.CPI.TOTL.ZG` latest available country observation since `2018`.

## Estimate
- High-market mean: `2.1700478684769005` over `43` countries.
- Low-market mean: `23.593463769866954` over `42` countries.
- Difference, high minus low: `-21.423415901390054`.
- Welch p-value: `0.0016507642551614517`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `167`.
- Market-score coefficient, standardized score: `-16.84970346499388`.
- Controlled p-value: `1.120068443276069e-29`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
