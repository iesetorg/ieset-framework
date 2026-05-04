# Result card — heritage_government_integrity_investment_share_income_region_robustness

**Verdict:** PARTIAL — controlled coefficient not decisive (coef=0.1563, p=0.8598)

## Design
- Heritage component: `government_integrity` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:NE.GDI.TOTL.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `23.557243235646563` over `40` countries.
- Low-market mean: `20.72884577743323` over `40` countries.
- Difference, high minus low: `2.8283974582133347`.
- Welch p-value: `0.14965968350620718`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `157`.
- Market-score coefficient, standardized score: `0.1563069978444626`.
- Controlled p-value: `0.8598064241323746`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
