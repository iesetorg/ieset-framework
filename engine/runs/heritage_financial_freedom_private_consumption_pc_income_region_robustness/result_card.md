# Result card — heritage_financial_freedom_private_consumption_pc_income_region_robustness

**Verdict:** SUPPORTED — controlled market-score coefficient has expected sign + and p=0.0001437

## Design
- Heritage component: `financial_freedom` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:NE.CON.PRVT.PC.KD` latest available country observation since `2018`.

## Estimate
- High-market mean: `15429.44789005316` over `60` countries.
- Low-market mean: `2376.7297932572633` over `55` countries.
- Difference, high minus low: `13052.718096795896`.
- Welch p-value: `4.366534901837061e-13`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `147`.
- Market-score coefficient, standardized score: `2608.2621810924165`.
- Controlled p-value: `0.00014370394513795812`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
