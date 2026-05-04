# Result card — heritage_economic_freedom_private_credit_depth_income_region_robustness

**Verdict:** SUPPORTED — controlled market-score coefficient has expected sign + and p=0.00419

## Design
- Heritage component: `overall_score` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:FS.AST.PRVT.GD.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `85.54424332712017` over `38` countries.
- Low-market mean: `28.36683450537158` over `38` countries.
- Difference, high minus low: `57.17740882174859`.
- Welch p-value: `2.2974560642669713e-08`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `151`.
- Market-score coefficient, standardized score: `11.26116417748743`.
- Controlled p-value: `0.004190482455218478`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
