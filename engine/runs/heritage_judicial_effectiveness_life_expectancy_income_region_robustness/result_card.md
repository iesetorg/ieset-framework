# Result card — heritage_judicial_effectiveness_life_expectancy_income_region_robustness

**Verdict:** SUPPORTED — controlled market-score coefficient has expected sign + and p=2.103e-06

## Design
- Heritage component: `judicial_effectiveness` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SP.DYN.LE00.IN` latest available country observation since `2018`.

## Estimate
- High-market mean: `79.95784498644986` over `45` countries.
- Low-market mean: `69.14371869918696` over `45` countries.
- Difference, high minus low: `10.814126287262894`.
- Welch p-value: `1.773316506486695e-16`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `174`.
- Market-score coefficient, standardized score: `1.4888597405718083`.
- Controlled p-value: `2.102860488624072e-06`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
