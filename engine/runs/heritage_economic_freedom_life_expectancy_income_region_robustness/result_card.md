# Result card — heritage_economic_freedom_life_expectancy_income_region_robustness

**Verdict:** SUPPORTED — controlled market-score coefficient has expected sign + and p=0.0006268

## Design
- Heritage component: `overall_score` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SP.DYN.LE00.IN` latest available country observation since `2018`.

## Estimate
- High-market mean: `79.96730654101997` over `44` countries.
- Low-market mean: `68.66273503325942` over `44` countries.
- Difference, high minus low: `11.304571507760542`.
- Welch p-value: `1.7720719008121838e-15`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `170`.
- Market-score coefficient, standardized score: `1.257701095634009`.
- Controlled p-value: `0.0006268174342718201`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
