# Result card — heritage_business_freedom_trade_openness_income_region_robustness

**Verdict:** PARTIAL — controlled coefficient not decisive (coef=12.33, p=0.1135)

## Design
- Heritage component: `business_freedom` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:NE.TRD.GNFS.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `121.2724301503683` over `40` countries.
- Low-market mean: `66.05664016865093` over `39` countries.
- Difference, high minus low: `55.215789981717364`.
- Welch p-value: `0.00013184294899587016`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `154`.
- Market-score coefficient, standardized score: `12.331838621293771`.
- Controlled p-value: `0.11352858338750203`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
