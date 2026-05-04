# Result card — heritage_financial_freedom_private_credit_depth_income_region_robustness

**Verdict:** SUPPORTED — controlled market-score coefficient has expected sign + and p=1.915e-05

## Design
- Heritage component: `financial_freedom` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:FS.AST.PRVT.GD.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `76.26690314196016` over `60` countries.
- Low-market mean: `33.34281069918175` over `56` countries.
- Difference, high minus low: `42.92409244277841`.
- Welch p-value: `7.410707749647597e-09`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `151`.
- Market-score coefficient, standardized score: `14.477826096608688`.
- Controlled p-value: `1.9148636101302986e-05`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
