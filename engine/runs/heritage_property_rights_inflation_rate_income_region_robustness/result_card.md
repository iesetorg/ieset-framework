# Result card — heritage_property_rights_inflation_rate_income_region_robustness

**Verdict:** SUPPORTED — controlled market-score coefficient has expected sign - and p=0.008515

## Design
- Heritage component: `property_rights` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:FP.CPI.TOTL.ZG` latest available country observation since `2018`.

## Estimate
- High-market mean: `2.5944552750845427` over `43` countries.
- Low-market mean: `19.116861865322587` over `43` countries.
- Difference, high minus low: `-16.522406590238045`.
- Welch p-value: `0.011721885836021994`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `171`.
- Market-score coefficient, standardized score: `-6.733488548885226`.
- Controlled p-value: `0.008514940620519905`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
