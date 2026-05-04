# Result card — heritage_property_rights_physician_density_income_region_robustness

**Verdict:** PARTIAL — controlled coefficient not decisive (coef=0.0804, p=0.4613)

## Design
- Heritage component: `property_rights` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SH.MED.PHYS.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `3.7048604651162798` over `43` countries.
- Low-market mean: `1.3054883720930233` over `43` countries.
- Difference, high minus low: `2.3993720930232563`.
- Welch p-value: `8.623514300292223e-10`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `166`.
- Market-score coefficient, standardized score: `0.0803977213076813`.
- Controlled p-value: `0.4613034960618705`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
