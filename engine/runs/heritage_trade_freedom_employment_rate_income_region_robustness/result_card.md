# Result card — heritage_trade_freedom_employment_rate_income_region_robustness

**Verdict:** SUPPORTED — controlled market-score coefficient has expected sign + and p=0.009424

## Design
- Heritage component: `trade_freedom` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SL.EMP.TOTL.SP.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `60.11736170212766` over `47` countries.
- Low-market mean: `57.17204651162792` over `43` countries.
- Difference, high minus low: `2.945315190499741`.
- Welch p-value: `0.22231159830781277`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `166`.
- Market-score coefficient, standardized score: `3.106721306549398`.
- Controlled p-value: `0.009424486339535089`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
