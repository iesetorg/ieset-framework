# Result card — heritage_property_rights_tertiary_enrollment_income_region_robustness

**Verdict:** PARTIAL — controlled coefficient not decisive (coef=2.591, p=0.3203)

## Design
- Heritage component: `property_rights` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SE.TER.ENRR` latest available country observation since `2018`.

## Estimate
- High-market mean: `77.8709963720304` over `37` countries.
- Low-market mean: `33.35306708762854` over `37` countries.
- Difference, high minus low: `44.517929284401866`.
- Welch p-value: `7.882343350495963e-12`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `143`.
- Market-score coefficient, standardized score: `2.5913749439945497`.
- Controlled p-value: `0.32029734138683247`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
