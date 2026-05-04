# Result card — heritage_trade_freedom_extreme_poverty_income_region_robustness

**Verdict:** PARTIAL — controlled coefficient not decisive (coef=1.544, p=0.2574)

## Design
- Heritage component: `trade_freedom` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SI.POV.DDAY` latest available country observation since `2018`.

## Estimate
- High-market mean: `0.9857142857142859` over `42` countries.
- Low-market mean: `27.703125` over `32` countries.
- Difference, high minus low: `-26.717410714285712`.
- Welch p-value: `8.094714387496073e-07`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `128`.
- Market-score coefficient, standardized score: `1.5438198519198245`.
- Controlled p-value: `0.2573601024921331`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
