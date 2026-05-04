# Result card — heritage_monetary_freedom_extreme_poverty_income_region_robustness

**Verdict:** PARTIAL — controlled coefficient not decisive (coef=-0.1846, p=0.853)

## Design
- Heritage component: `monetary_freedom` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SI.POV.DDAY` latest available country observation since `2018`.

## Estimate
- High-market mean: `6.397058823529411` over `34` countries.
- Low-market mean: `20.668750000000003` over `32` countries.
- Difference, high minus low: `-14.271691176470592`.
- Welch p-value: `0.00930171579008012`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `127`.
- Market-score coefficient, standardized score: `-0.18457030873851413`.
- Controlled p-value: `0.8530204009648031`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
