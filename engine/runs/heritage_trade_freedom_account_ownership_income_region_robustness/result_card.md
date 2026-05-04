# Result card — heritage_trade_freedom_account_ownership_income_region_robustness

**Verdict:** PARTIAL — controlled coefficient not decisive (coef=-0.6145, p=0.7044)

## Design
- Heritage component: `trade_freedom` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:FX.OWN.TOTL.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `89.9588161506619` over `44` countries.
- Low-market mean: `57.93451478946118` over `36` countries.
- Difference, high minus low: `32.02430136120072`.
- Welch p-value: `2.162381805656254e-11`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `136`.
- Market-score coefficient, standardized score: `-0.614475209753555`.
- Controlled p-value: `0.7044450819249599`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
