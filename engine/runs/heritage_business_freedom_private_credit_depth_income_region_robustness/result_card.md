# Result card — heritage_business_freedom_private_credit_depth_income_region_robustness

**Verdict:** SUPPORTED — controlled market-score coefficient has expected sign + and p=3.544e-05

## Design
- Heritage component: `business_freedom` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:FS.AST.PRVT.GD.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `85.61910992384584` over `38` countries.
- Low-market mean: `18.27406540985964` over `40` countries.
- Difference, high minus low: `67.3450445139862`.
- Welch p-value: `1.8661338444329576e-11`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `151`.
- Market-score coefficient, standardized score: `22.48512965208024`.
- Controlled p-value: `3.544254268512249e-05`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
