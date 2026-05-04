# Result card — heritage_trade_freedom_high_tech_exports_income_region_robustness

**Verdict:** PARTIAL — controlled coefficient not decisive (coef=1.363, p=0.2645)

## Design
- Heritage component: `trade_freedom` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:TX.VAL.TECH.MF.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `18.441607791910215` over `49` countries.
- Low-market mean: `5.080655306089287` over `42` countries.
- Difference, high minus low: `13.360952485820928`.
- Welch p-value: `6.252238531099035e-07`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `160`.
- Market-score coefficient, standardized score: `1.3625714055437261`.
- Controlled p-value: `0.2644578329998173`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
