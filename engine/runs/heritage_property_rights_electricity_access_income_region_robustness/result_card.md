# Result card — heritage_property_rights_electricity_access_income_region_robustness

**Verdict:** PARTIAL — controlled coefficient not decisive (coef=-1.623, p=0.2634)

## Design
- Heritage component: `property_rights` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:EG.ELC.ACCS.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `99.37555555555555` over `45` countries.
- Low-market mean: `73.09777777777778` over `45` countries.
- Difference, high minus low: `26.27777777777777`.
- Welch p-value: `1.89255234166189e-07`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `173`.
- Market-score coefficient, standardized score: `-1.6233560373838092`.
- Controlled p-value: `0.26342432999202875`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
