# Result card — heritage_tax_burden_extreme_poverty_income_region_robustness

**Verdict:** PARTIAL — controlled coefficient not decisive (coef=-1.28, p=0.2307)

## Design
- Heritage component: `tax_burden` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SI.POV.DDAY` latest available country observation since `2018`.

## Estimate
- High-market mean: `8.539393939393937` over `33` countries.
- Low-market mean: `7.2437499999999995` over `32` countries.
- Difference, high minus low: `1.2956439393939378`.
- Welch p-value: `0.7399237255074114`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `127`.
- Market-score coefficient, standardized score: `-1.2802148968603968`.
- Controlled p-value: `0.23074765951932677`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
