# Result card — heritage_economic_freedom_private_consumption_pc_income_region_robustness

**Verdict:** SUPPORTED — controlled market-score coefficient has expected sign + and p=7.864e-06

## Design
- Heritage component: `overall_score` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:NE.CON.PRVT.PC.KD` latest available country observation since `2018`.

## Estimate
- High-market mean: `19688.819607227975` over `37` countries.
- Low-market mean: `2169.066205341057` over `37` countries.
- Difference, high minus low: `17519.75340188692`.
- Welch p-value: `8.971317527374089e-12`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `147`.
- Market-score coefficient, standardized score: `3512.9691429355375`.
- Controlled p-value: `7.864116342423296e-06`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
