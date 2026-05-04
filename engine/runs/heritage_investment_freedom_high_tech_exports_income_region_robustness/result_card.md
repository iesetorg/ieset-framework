# Result card — heritage_investment_freedom_high_tech_exports_income_region_robustness

**Verdict:** PARTIAL — controlled coefficient not decisive (coef=1.799, p=0.1445)

## Design
- Heritage component: `investment_freedom` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:TX.VAL.TECH.MF.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `15.837870808141757` over `58` countries.
- Low-market mean: `9.830139707491377` over `51` countries.
- Difference, high minus low: `6.00773110065038`.
- Welch p-value: `0.024750701500410574`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `159`.
- Market-score coefficient, standardized score: `1.798985826717593`.
- Controlled p-value: `0.14451632817393187`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
