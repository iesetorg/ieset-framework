# Result card — heritage_government_integrity_extreme_poverty_income_region_robustness

**Verdict:** REFUTED — controlled market-score coefficient has opposite sign and p=0.03691

## Design
- Heritage component: `government_integrity` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SI.POV.DDAY` latest available country observation since `2018`.

## Estimate
- High-market mean: `0.5272727272727273` over `33` countries.
- Low-market mean: `25.645454545454545` over `33` countries.
- Difference, high minus low: `-25.118181818181817`.
- Welch p-value: `9.013818400115915e-06`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `129`.
- Market-score coefficient, standardized score: `3.0757940281939486`.
- Controlled p-value: `0.03691277324946538`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
