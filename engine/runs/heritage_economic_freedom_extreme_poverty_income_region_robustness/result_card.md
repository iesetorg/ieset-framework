# Result card — heritage_economic_freedom_extreme_poverty_income_region_robustness

**Verdict:** PARTIAL — controlled coefficient not decisive (coef=1.933, p=0.1984)

## Design
- Heritage component: `overall_score` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SI.POV.DDAY` latest available country observation since `2018`.

## Estimate
- High-market mean: `0.59375` over `32` countries.
- Low-market mean: `26.175` over `32` countries.
- Difference, high minus low: `-25.58125`.
- Welch p-value: `1.8138604343922438e-05`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `127`.
- Market-score coefficient, standardized score: `1.9326433588882064`.
- Controlled p-value: `0.1984008644757508`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
