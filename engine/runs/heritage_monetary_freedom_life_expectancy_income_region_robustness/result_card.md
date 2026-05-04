# Result card — heritage_monetary_freedom_life_expectancy_income_region_robustness

**Verdict:** PARTIAL — controlled coefficient not decisive (coef=0.02772, p=0.9123)

## Design
- Heritage component: `monetary_freedom` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SP.DYN.LE00.IN` latest available country observation since `2018`.

## Estimate
- High-market mean: `75.86905931263858` over `44` countries.
- Low-market mean: `70.94365311653117` over `45` countries.
- Difference, high minus low: `4.925406196107417`.
- Welch p-value: `0.0005238276877884327`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `170`.
- Market-score coefficient, standardized score: `0.027717779536293955`.
- Controlled p-value: `0.9123303669685776`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
