# Result card — heritage_property_rights_extreme_poverty_income_region_robustness

**Verdict:** REFUTED — controlled market-score coefficient has opposite sign and p=0.02749

## Design
- Heritage component: `property_rights` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SI.POV.DDAY` latest available country observation since `2018`.

## Estimate
- High-market mean: `0.41515151515151516` over `33` countries.
- Low-market mean: `24.763636363636365` over `33` countries.
- Difference, high minus low: `-24.34848484848485`.
- Welch p-value: `1.3590777913082726e-05`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `129`.
- Market-score coefficient, standardized score: `3.2642878631122167`.
- Controlled p-value: `0.027486802887644237`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
