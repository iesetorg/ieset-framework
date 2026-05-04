# Result card — heritage_business_freedom_female_lfp_income_region_robustness

**Verdict:** PARTIAL — controlled coefficient not decisive (coef=3.033, p=0.1461)

## Design
- Heritage component: `business_freedom` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SL.TLF.CACT.FE.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `56.315069767441855` over `43` countries.
- Low-market mean: `55.3338409090909` over `44` countries.
- Difference, high minus low: `0.9812288583509527`.
- Welch p-value: `0.7477285057874781`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `165`.
- Market-score coefficient, standardized score: `3.0326250563434556`.
- Controlled p-value: `0.1460811550287373`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
