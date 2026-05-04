# Result card — heritage_property_rights_high_tech_exports_income_region_robustness

**Verdict:** SUPPORTED — controlled market-score coefficient has expected sign + and p=0.002853

## Design
- Heritage component: `property_rights` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:TX.VAL.TECH.MF.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `21.5415457001962` over `42` countries.
- Low-market mean: `3.967735707566968` over `41` countries.
- Difference, high minus low: `17.57380999262923`.
- Welch p-value: `1.638026516460477e-08`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `162`.
- Market-score coefficient, standardized score: `4.1577540434451095`.
- Controlled p-value: `0.0028532012219140788`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
