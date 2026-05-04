# Result card — heritage_property_rights_under5_mortality_income_region_robustness

**Verdict:** SUPPORTED — controlled market-score coefficient has expected sign - and p=0.01208

## Design
- Heritage component: `property_rights` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SH.DYN.MORT` latest available country observation since `2018`.

## Estimate
- High-market mean: `6.466666666666665` over `45` countries.
- Low-market mean: `41.864444444444445` over `45` countries.
- Difference, high minus low: `-35.397777777777776`.
- Welch p-value: `6.060965653191115e-10`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `174`.
- Market-score coefficient, standardized score: `-3.770348459748796`.
- Controlled p-value: `0.012075985114531444`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
