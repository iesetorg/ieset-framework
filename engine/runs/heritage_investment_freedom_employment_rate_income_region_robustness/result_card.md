# Result card — heritage_investment_freedom_employment_rate_income_region_robustness

**Verdict:** PARTIAL — controlled coefficient not decisive (coef=1.859, p=0.1126)

## Design
- Heritage component: `investment_freedom` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SL.EMP.TOTL.SP.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `58.47222413793103` over `58` countries.
- Low-market mean: `56.808` over `43` countries.
- Difference, high minus low: `1.6642241379310292`.
- Welch p-value: `0.45376127671631805`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `165`.
- Market-score coefficient, standardized score: `1.8592317678999704`.
- Controlled p-value: `0.11261768446407135`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
