# Result card — heritage_labor_freedom_tertiary_enrollment_income_region_robustness

**Verdict:** PARTIAL — controlled coefficient not decisive (coef=2.681, p=0.2007)

## Design
- Heritage component: `labor_freedom` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SE.TER.ENRR` latest available country observation since `2018`.

## Estimate
- High-market mean: `69.03701669528006` over `36` countries.
- Low-market mean: `32.42308899116168` over `36` countries.
- Difference, high minus low: `36.61392770411838`.
- Welch p-value: `4.794684454376984e-08`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `141`.
- Market-score coefficient, standardized score: `2.6812562095626125`.
- Controlled p-value: `0.2006622017133385`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
