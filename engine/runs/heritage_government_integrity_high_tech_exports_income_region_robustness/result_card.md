# Result card — heritage_government_integrity_high_tech_exports_income_region_robustness

**Verdict:** SUPPORTED — controlled market-score coefficient has expected sign + and p=0.01783

## Design
- Heritage component: `government_integrity` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:TX.VAL.TECH.MF.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `18.210250850001067` over `41` countries.
- Low-market mean: `4.791003274041143` over `41` countries.
- Difference, high minus low: `13.419247575959925`.
- Welch p-value: `6.682393837186192e-07`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `162`.
- Market-score coefficient, standardized score: `3.204915164789002`.
- Controlled p-value: `0.017832281401653233`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
