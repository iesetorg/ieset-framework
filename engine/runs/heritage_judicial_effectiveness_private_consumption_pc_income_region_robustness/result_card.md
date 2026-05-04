# Result card — heritage_judicial_effectiveness_private_consumption_pc_income_region_robustness

**Verdict:** SUPPORTED — controlled market-score coefficient has expected sign + and p=3.265e-09

## Design
- Heritage component: `judicial_effectiveness` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:NE.CON.PRVT.PC.KD` latest available country observation since `2018`.

## Estimate
- High-market mean: `20302.339960965095` over `38` countries.
- Low-market mean: `2336.477317008988` over `38` countries.
- Difference, high minus low: `17965.86264395611`.
- Welch p-value: `3.8542607168435214e-13`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `150`.
- Market-score coefficient, standardized score: `3966.8427535375777`.
- Controlled p-value: `3.2645160364349996e-09`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
