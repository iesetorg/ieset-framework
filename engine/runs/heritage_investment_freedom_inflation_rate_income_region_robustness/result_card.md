# Result card — heritage_investment_freedom_inflation_rate_income_region_robustness

**Verdict:** SUPPORTED — controlled market-score coefficient has expected sign - and p=0.003066

## Design
- Heritage component: `investment_freedom` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:FP.CPI.TOTL.ZG` latest available country observation since `2018`.

## Estimate
- High-market mean: `4.00763716134024` over `59` countries.
- Low-market mean: `12.610537100010257` over `54` countries.
- Difference, high minus low: `-8.602899938670017`.
- Welch p-value: `0.015007559291585447`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `167`.
- Market-score coefficient, standardized score: `-6.678460574904107`.
- Controlled p-value: `0.003065574356675984`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
