# Result card — heritage_tax_burden_life_expectancy_income_region_robustness

**Verdict:** REFUTED — controlled market-score coefficient has opposite sign and p=0.0005532

## Design
- Heritage component: `tax_burden` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SP.DYN.LE00.IN` latest available country observation since `2018`.

## Estimate
- High-market mean: `74.46313248337029` over `44` countries.
- Low-market mean: `76.65108314855875` over `44` countries.
- Difference, high minus low: `-2.187950665188467`.
- Welch p-value: `0.13863838822137262`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `171`.
- Market-score coefficient, standardized score: `-0.8943522084802021`.
- Controlled p-value: `0.0005531739162633525`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
