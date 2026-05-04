# Result card — heritage_trade_freedom_under5_mortality_income_region_robustness

**Verdict:** PARTIAL — controlled coefficient not decisive (coef=-0.8158, p=0.5491)

## Design
- Heritage component: `trade_freedom` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SH.DYN.MORT` latest available country observation since `2018`.

## Estimate
- High-market mean: `7.472` over `50` countries.
- Low-market mean: `40.36136363636364` over `44` countries.
- Difference, high minus low: `-32.88936363636364`.
- Welch p-value: `3.4630264515670206e-10`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `171`.
- Market-score coefficient, standardized score: `-0.8157924945263428`.
- Controlled p-value: `0.5491268651890191`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
