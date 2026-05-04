# Result card — heritage_economic_freedom_tertiary_enrollment_income_region_robustness

**Verdict:** PARTIAL — controlled coefficient not decisive (coef=2.437, p=0.3552)

## Design
- Heritage component: `overall_score` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SE.TER.ENRR` latest available country observation since `2018`.

## Estimate
- High-market mean: `76.03351768892539` over `36` countries.
- Low-market mean: `29.364804503817066` over `36` countries.
- Difference, high minus low: `46.66871318510832`.
- Welch p-value: `1.0400372463985775e-11`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `141`.
- Market-score coefficient, standardized score: `2.436994791301647`.
- Controlled p-value: `0.3552473156095567`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
