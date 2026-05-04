# Result card — heritage_government_integrity_under5_mortality_income_region_robustness

**Verdict:** SUPPORTED — controlled market-score coefficient has expected sign - and p=0.07665

## Design
- Heritage component: `government_integrity` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SH.DYN.MORT` latest available country observation since `2018`.

## Estimate
- High-market mean: `6.755555555555555` over `45` countries.
- Low-market mean: `43.61555555555556` over `45` countries.
- Difference, high minus low: `-36.86000000000001`.
- Welch p-value: `1.1387895012006771e-11`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `174`.
- Market-score coefficient, standardized score: `-2.565333920431071`.
- Controlled p-value: `0.07664637723081553`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
