# Result card — heritage_government_spending_employment_rate_income_region_robustness

**Verdict:** PARTIAL — controlled coefficient not decisive (coef=0.2314, p=0.8494)

## Design
- Heritage component: `government_spending` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SL.EMP.TOTL.SP.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `57.89123255813954` over `43` countries.
- Low-market mean: `58.02867441860465` over `43` countries.
- Difference, high minus low: `-0.13744186046510976`.
- Welch p-value: `0.9538442622164541`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `165`.
- Market-score coefficient, standardized score: `0.2314499183361058`.
- Controlled p-value: `0.8493813527428806`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
