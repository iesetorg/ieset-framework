# Result card — heritage_investment_freedom_tertiary_enrollment_income_region_robustness

**Verdict:** PARTIAL — controlled coefficient not decisive (coef=1.723, p=0.4509)

## Design
- Heritage component: `investment_freedom` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SE.TER.ENRR` latest available country observation since `2018`.

## Estimate
- High-market mean: `68.57283920626568` over `56` countries.
- Low-market mean: `32.99780374725167` over `44` countries.
- Difference, high minus low: `35.57503545901401`.
- Welch p-value: `3.463811538158343e-11`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `141`.
- Market-score coefficient, standardized score: `1.7225526802099316`.
- Controlled p-value: `0.45088178587754624`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
