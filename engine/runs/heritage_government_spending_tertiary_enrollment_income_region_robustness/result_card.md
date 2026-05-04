# Result card — heritage_government_spending_tertiary_enrollment_income_region_robustness

**Verdict:** REFUTED — controlled market-score coefficient has opposite sign and p=0.01484

## Design
- Heritage component: `government_spending` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SE.TER.ENRR` latest available country observation since `2018`.

## Estimate
- High-market mean: `27.48667523163536` over `36` countries.
- Low-market mean: `68.60609921865611` over `36` countries.
- Difference, high minus low: `-41.11942398702075`.
- Welch p-value: `9.692796481915311e-09`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `141`.
- Market-score coefficient, standardized score: `-5.231106169912294`.
- Controlled p-value: `0.014842750892198772`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
