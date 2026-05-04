# Result card — heritage_financial_freedom_extreme_poverty_income_region_robustness

**Verdict:** REFUTED — controlled market-score coefficient has opposite sign and p=0.009612

## Design
- Heritage component: `financial_freedom` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SI.POV.DDAY` latest available country observation since `2018`.

## Estimate
- High-market mean: `1.430612244897959` over `49` countries.
- Low-market mean: `20.627659574468087` over `47` countries.
- Difference, high minus low: `-19.19704732957013`.
- Welch p-value: `1.132929445531082e-06`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `127`.
- Market-score coefficient, standardized score: `3.3000611875601855`.
- Controlled p-value: `0.009611624130427201`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
