# Result card — heritage_government_spending_private_consumption_pc_income_region_robustness

**Verdict:** REFUTED — controlled market-score coefficient has opposite sign and p=0.0005494

## Design
- Heritage component: `government_spending` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:NE.CON.PRVT.PC.KD` latest available country observation since `2018`.

## Estimate
- High-market mean: `2615.553297351854` over `37` countries.
- Low-market mean: `15613.881415227888` over `37` countries.
- Difference, high minus low: `-12998.328117876034`.
- Welch p-value: `1.230796089503238e-09`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `147`.
- Market-score coefficient, standardized score: `-2231.6409417076693`.
- Controlled p-value: `0.0005493777312698716`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
