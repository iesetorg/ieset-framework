# Result card — heritage_tax_burden_tertiary_enrollment_income_region_robustness

**Verdict:** REFUTED — controlled market-score coefficient has opposite sign and p=0.004933

## Design
- Heritage component: `tax_burden` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SE.TER.ENRR` latest available country observation since `2018`.

## Estimate
- High-market mean: `51.48786378926056` over `36` countries.
- Low-market mean: `68.03682166208006` over `36` countries.
- Difference, high minus low: `-16.5489578728195`.
- Welch p-value: `0.019664132281885204`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `141`.
- Market-score coefficient, standardized score: `-5.16727077999085`.
- Controlled p-value: `0.004933106529146597`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
