# Result card — heritage_business_freedom_investment_share_income_region_robustness

**Verdict:** PARTIAL — controlled coefficient not decisive (coef=0.7715, p=0.5394)

## Design
- Heritage component: `business_freedom` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:NE.GDI.TOTL.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `22.37493583087184` over `40` countries.
- Low-market mean: `20.93254231329803` over `39` countries.
- Difference, high minus low: `1.4423935175738123`.
- Welch p-value: `0.43138990381874165`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `153`.
- Market-score coefficient, standardized score: `0.7715063850974064`.
- Controlled p-value: `0.5394324312498252`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
