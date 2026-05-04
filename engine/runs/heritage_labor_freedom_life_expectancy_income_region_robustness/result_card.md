# Result card — heritage_labor_freedom_life_expectancy_income_region_robustness

**Verdict:** PARTIAL — controlled coefficient not decisive (coef=-0.2293, p=0.4344)

## Design
- Heritage component: `labor_freedom` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SP.DYN.LE00.IN` latest available country observation since `2018`.

## Estimate
- High-market mean: `77.14158590785908` over `45` countries.
- Low-market mean: `69.68187416851441` over `44` countries.
- Difference, high minus low: `7.4597117393446695`.
- Welch p-value: `5.4052990878983504e-08`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `170`.
- Market-score coefficient, standardized score: `-0.22933901805249435`.
- Controlled p-value: `0.434376002877915`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
