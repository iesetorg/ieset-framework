# Result card — heritage_trade_freedom_private_consumption_pc_income_region_robustness

**Verdict:** PARTIAL — controlled coefficient not decisive (coef=818.7, p=0.2454)

## Design
- Heritage component: `trade_freedom` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:NE.CON.PRVT.PC.KD` latest available country observation since `2018`.

## Estimate
- High-market mean: `16384.572469316045` over `49` countries.
- Low-market mean: `2219.9361439491904` over `38` countries.
- Difference, high minus low: `14164.636325366853`.
- Welch p-value: `7.076927496890106e-13`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `148`.
- Market-score coefficient, standardized score: `818.6753994448986`.
- Controlled p-value: `0.24540660827454724`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
