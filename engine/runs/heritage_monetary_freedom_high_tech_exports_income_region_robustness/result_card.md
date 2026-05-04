# Result card — heritage_monetary_freedom_high_tech_exports_income_region_robustness

**Verdict:** PARTIAL — controlled coefficient not decisive (coef=0.9, p=0.346)

## Design
- Heritage component: `monetary_freedom` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:TX.VAL.TECH.MF.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `12.686750575947775` over `42` countries.
- Low-market mean: `7.281033972215836` over `40` countries.
- Difference, high minus low: `5.405716603731939`.
- Welch p-value: `0.06461627210504296`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `159`.
- Market-score coefficient, standardized score: `0.8999543157831355`.
- Controlled p-value: `0.3460199371304631`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
