# Result card — heritage_financial_freedom_high_tech_exports_income_region_robustness

**Verdict:** PARTIAL — controlled coefficient not decisive (coef=1.183, p=0.3386)

## Design
- Heritage component: `financial_freedom` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:TX.VAL.TECH.MF.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `14.986837747073437` over `64` countries.
- Low-market mean: `7.272346123080792` over `59` countries.
- Difference, high minus low: `7.714491623992645`.
- Welch p-value: `0.0006664262301919718`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `159`.
- Market-score coefficient, standardized score: `1.1831732492974145`.
- Controlled p-value: `0.33864261828213815`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
