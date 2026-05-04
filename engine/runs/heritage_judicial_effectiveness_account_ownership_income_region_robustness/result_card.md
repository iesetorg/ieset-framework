# Result card — heritage_judicial_effectiveness_account_ownership_income_region_robustness

**Verdict:** SUPPORTED — controlled market-score coefficient has expected sign + and p=9.111e-06

## Design
- Heritage component: `judicial_effectiveness` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:FX.OWN.TOTL.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `94.29473452587496` over `36` countries.
- Low-market mean: `47.07402552545637` over `36` countries.
- Difference, high minus low: `47.22070900041859`.
- Welch p-value: `9.213009858151728e-18`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `139`.
- Market-score coefficient, standardized score: `7.307661665125037`.
- Controlled p-value: `9.11148947375558e-06`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
