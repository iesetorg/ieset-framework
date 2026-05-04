# Result card — heritage_trade_freedom_investment_share_income_region_robustness

**Verdict:** PARTIAL — controlled coefficient not decisive (coef=0.1178, p=0.8839)

## Design
- Heritage component: `trade_freedom` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:NE.GDI.TOTL.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `23.254693276659886` over `50` countries.
- Low-market mean: `23.648294645004075` over `39` countries.
- Difference, high minus low: `-0.39360136834418924`.
- Welch p-value: `0.8393939796437461`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `154`.
- Market-score coefficient, standardized score: `0.11780481742461858`.
- Controlled p-value: `0.8838804798335802`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
