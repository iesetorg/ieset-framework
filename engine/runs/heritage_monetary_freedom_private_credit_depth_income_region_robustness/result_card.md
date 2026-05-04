# Result card — heritage_monetary_freedom_private_credit_depth_income_region_robustness

**Verdict:** SUPPORTED — controlled market-score coefficient has expected sign + and p=0.02022

## Design
- Heritage component: `monetary_freedom` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:FS.AST.PRVT.GD.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `64.80920707566077` over `38` countries.
- Low-market mean: `31.628599250439862` over `38` countries.
- Difference, high minus low: `33.1806078252209`.
- Welch p-value: `0.0002446687952164024`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `151`.
- Market-score coefficient, standardized score: `6.293826021153765`.
- Controlled p-value: `0.020220490047309213`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
