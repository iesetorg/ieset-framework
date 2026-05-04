# Result card — heritage_labor_freedom_private_consumption_pc_income_region_robustness

**Verdict:** SUPPORTED — controlled market-score coefficient has expected sign + and p=0.02613

## Design
- Heritage component: `labor_freedom` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:NE.CON.PRVT.PC.KD` latest available country observation since `2018`.

## Estimate
- High-market mean: `16947.44396746856` over `38` countries.
- Low-market mean: `2634.53292086204` over `37` countries.
- Difference, high minus low: `14312.91104660652`.
- Welch p-value: `2.845549572070016e-10`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `147`.
- Market-score coefficient, standardized score: `1412.0528419680847`.
- Controlled p-value: `0.02612558734368165`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
