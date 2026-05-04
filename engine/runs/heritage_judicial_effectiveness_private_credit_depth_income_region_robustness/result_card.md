# Result card — heritage_judicial_effectiveness_private_credit_depth_income_region_robustness

**Verdict:** SUPPORTED — controlled market-score coefficient has expected sign + and p=0.002134

## Design
- Heritage component: `judicial_effectiveness` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:FS.AST.PRVT.GD.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `82.54774582470993` over `39` countries.
- Low-market mean: `26.5066089014496` over `39` countries.
- Difference, high minus low: `56.04113692326034`.
- Welch p-value: `3.005836110975566e-09`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `155`.
- Market-score coefficient, standardized score: `10.462124485882631`.
- Controlled p-value: `0.002134166717499167`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
