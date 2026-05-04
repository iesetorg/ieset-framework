# Result card — heritage_financial_freedom_tertiary_enrollment_income_region_robustness

**Verdict:** SUPPORTED — controlled market-score coefficient has expected sign + and p=0.01379

## Design
- Heritage component: `financial_freedom` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SE.TER.ENRR` latest available country observation since `2018`.

## Estimate
- High-market mean: `73.40470684598478` over `36` countries.
- Low-market mean: `27.900241690811878` over `47` countries.
- Difference, high minus low: `45.504465155172895`.
- Welch p-value: `6.467668190663822e-16`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `141`.
- Market-score coefficient, standardized score: `5.324081970740276`.
- Controlled p-value: `0.013785437554415922`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
