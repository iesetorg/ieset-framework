# Result card — heritage_government_integrity_private_credit_depth_income_region_robustness

**Verdict:** SUPPORTED — controlled market-score coefficient has expected sign + and p=7.904e-07

## Design
- Heritage component: `government_integrity` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:FS.AST.PRVT.GD.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `83.691321111596` over `39` countries.
- Low-market mean: `24.273728531887546` over `39` countries.
- Difference, high minus low: `59.417592579708455`.
- Welch p-value: `9.785088661047226e-10`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `155`.
- Market-score coefficient, standardized score: `17.874185000139544`.
- Controlled p-value: `7.90433513662366e-07`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
