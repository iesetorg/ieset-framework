# Result card — heritage_property_rights_private_consumption_pc_income_region_robustness

**Verdict:** SUPPORTED — controlled market-score coefficient has expected sign + and p=4.2e-10

## Design
- Heritage component: `property_rights` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:NE.CON.PRVT.PC.KD` latest available country observation since `2018`.

## Estimate
- High-market mean: `20972.74650639725` over `38` countries.
- Low-market mean: `2140.978760013978` over `38` countries.
- Difference, high minus low: `18831.76774638327`.
- Welch p-value: `9.700151434929221e-15`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `150`.
- Market-score coefficient, standardized score: `4633.803247426749`.
- Controlled p-value: `4.2003968379095603e-10`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
