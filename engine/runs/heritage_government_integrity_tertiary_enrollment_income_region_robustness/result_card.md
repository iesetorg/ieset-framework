# Result card — heritage_government_integrity_tertiary_enrollment_income_region_robustness

**Verdict:** SUPPORTED — controlled market-score coefficient has expected sign + and p=0.07756

## Design
- Heritage component: `government_integrity` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SE.TER.ENRR` latest available country observation since `2018`.

## Estimate
- High-market mean: `74.18763543493486` over `38` countries.
- Low-market mean: `28.10007640031204` over `37` countries.
- Difference, high minus low: `46.08755903462282`.
- Welch p-value: `4.849178346534861e-13`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `143`.
- Market-score coefficient, standardized score: `4.4094528139389375`.
- Controlled p-value: `0.07756043106866041`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
