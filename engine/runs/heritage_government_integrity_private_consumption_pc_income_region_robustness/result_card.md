# Result card — heritage_government_integrity_private_consumption_pc_income_region_robustness

**Verdict:** SUPPORTED — controlled market-score coefficient has expected sign + and p=3.547e-17

## Design
- Heritage component: `government_integrity` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:NE.CON.PRVT.PC.KD` latest available country observation since `2018`.

## Estimate
- High-market mean: `20405.802959899425` over `39` countries.
- Low-market mean: `1802.3594587623054` over `38` countries.
- Difference, high minus low: `18603.44350113712`.
- Welch p-value: `6.646953852220957e-14`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `150`.
- Market-score coefficient, standardized score: `5798.042098733208`.
- Controlled p-value: `3.5466753019678194e-17`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
