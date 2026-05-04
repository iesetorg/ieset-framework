# Result card — heritage_property_rights_investment_share_income_region_robustness

**Verdict:** PARTIAL — controlled coefficient not decisive (coef=0.6426, p=0.4875)

## Design
- Heritage component: `property_rights` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:NE.GDI.TOTL.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `22.605380985449994` over `40` countries.
- Low-market mean: `20.910497658955478` over `40` countries.
- Difference, high minus low: `1.6948833264945158`.
- Welch p-value: `0.3570286172166337`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `157`.
- Market-score coefficient, standardized score: `0.6425503064256951`.
- Controlled p-value: `0.4874931767342934`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
