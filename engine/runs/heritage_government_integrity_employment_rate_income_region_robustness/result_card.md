# Result card — heritage_government_integrity_employment_rate_income_region_robustness

**Verdict:** SUPPORTED — controlled market-score coefficient has expected sign + and p=0.08487

## Design
- Heritage component: `government_integrity` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SL.EMP.TOTL.SP.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `59.34125000000001` over `44` countries.
- Low-market mean: `55.40886363636364` over `44` countries.
- Difference, high minus low: `3.9323863636363683`.
- Welch p-value: `0.1314910636343735`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `169`.
- Market-score coefficient, standardized score: `2.2734066423002686`.
- Controlled p-value: `0.08486911613522906`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
