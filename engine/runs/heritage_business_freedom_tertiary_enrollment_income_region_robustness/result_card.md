# Result card — heritage_business_freedom_tertiary_enrollment_income_region_robustness

**Verdict:** SUPPORTED — controlled market-score coefficient has expected sign + and p=0.05773

## Design
- Heritage component: `business_freedom` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SE.TER.ENRR` latest available country observation since `2018`.

## Estimate
- High-market mean: `79.2916650982099` over `37` countries.
- Low-market mean: `19.526355915513744` over `36` countries.
- Difference, high minus low: `59.76530918269616`.
- Welch p-value: `1.302327506885006e-21`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `141`.
- Market-score coefficient, standardized score: `6.291615573854614`.
- Controlled p-value: `0.057734076058916894`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
