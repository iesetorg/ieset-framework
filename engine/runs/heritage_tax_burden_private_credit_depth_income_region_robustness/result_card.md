# Result card — heritage_tax_burden_private_credit_depth_income_region_robustness

**Verdict:** REFUTED — controlled market-score coefficient has opposite sign and p=6.613e-05

## Design
- Heritage component: `tax_burden` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:FS.AST.PRVT.GD.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `49.48217477090786` over `38` countries.
- Low-market mean: `78.34684141948178` over `38` countries.
- Difference, high minus low: `-28.864666648573916`.
- Welch p-value: `0.0035017094389201177`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `152`.
- Market-score coefficient, standardized score: `-10.921675069906586`.
- Controlled p-value: `6.613074377527968e-05`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
