# Result card — heritage_property_rights_private_credit_depth_income_region_robustness

**Verdict:** SUPPORTED — controlled market-score coefficient has expected sign + and p=9.117e-06

## Design
- Heritage component: `property_rights` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:FS.AST.PRVT.GD.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `82.45033361100303` over `39` countries.
- Low-market mean: `23.744763091596255` over `39` countries.
- Difference, high minus low: `58.70557051940678`.
- Welch p-value: `1.0928882825108399e-09`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `155`.
- Market-score coefficient, standardized score: `16.9648154245315`.
- Controlled p-value: `9.117193103800085e-06`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
