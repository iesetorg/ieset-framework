# Result card — heritage_labor_freedom_extreme_poverty_income_region_robustness

**Verdict:** PARTIAL — controlled coefficient not decisive (coef=0.8382, p=0.4779)

## Design
- Heritage component: `labor_freedom` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SI.POV.DDAY` latest available country observation since `2018`.

## Estimate
- High-market mean: `2.5999999999999996` over `33` countries.
- Low-market mean: `21.821875` over `32` countries.
- Difference, high minus low: `-19.221874999999997`.
- Welch p-value: `0.0001846055380399047`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `127`.
- Market-score coefficient, standardized score: `0.8381848763586469`.
- Controlled p-value: `0.4778928564134787`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
