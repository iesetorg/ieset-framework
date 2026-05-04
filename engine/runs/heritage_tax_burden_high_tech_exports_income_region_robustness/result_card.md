# Result card — heritage_tax_burden_high_tech_exports_income_region_robustness

**Verdict:** REFUTED — controlled market-score coefficient has opposite sign and p=0.0414

## Design
- Heritage component: `tax_burden` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:TX.VAL.TECH.MF.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `8.330694514068199` over `41` countries.
- Low-market mean: `15.03201258964907` over `41` countries.
- Difference, high minus low: `-6.701318075580872`.
- Welch p-value: `0.009281324975604839`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `160`.
- Market-score coefficient, standardized score: `-2.0123646293175783`.
- Controlled p-value: `0.041402659054727405`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
