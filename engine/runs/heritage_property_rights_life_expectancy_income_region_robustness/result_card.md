# Result card — heritage_property_rights_life_expectancy_income_region_robustness

**Verdict:** SUPPORTED — controlled market-score coefficient has expected sign + and p=5.307e-08

## Design
- Heritage component: `property_rights` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SP.DYN.LE00.IN` latest available country observation since `2018`.

## Estimate
- High-market mean: `80.53482005420054` over `45` countries.
- Low-market mean: `68.52381842818427` over `45` countries.
- Difference, high minus low: `12.011001626016267`.
- Welch p-value: `2.3488564122439738e-17`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `174`.
- Market-score coefficient, standardized score: `1.8948278807113232`.
- Controlled p-value: `5.3071110244370806e-08`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
