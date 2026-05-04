# Result card — heritage_labor_freedom_inflation_rate_income_region_robustness

**Verdict:** SUPPORTED — controlled market-score coefficient has expected sign - and p=0.02129

## Design
- Heritage component: `labor_freedom` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:FP.CPI.TOTL.ZG` latest available country observation since `2018`.

## Estimate
- High-market mean: `3.8722068946728716` over `43` countries.
- Low-market mean: `14.15822368332757` over `42` countries.
- Difference, high minus low: `-10.286016788654699`.
- Welch p-value: `0.016181472778181098`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `167`.
- Market-score coefficient, standardized score: `-4.887880755315684`.
- Controlled p-value: `0.021287325232897558`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
