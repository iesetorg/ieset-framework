# Result card — heritage_property_rights_trade_openness_income_region_robustness

**Verdict:** PARTIAL — controlled coefficient not decisive (coef=5.846, p=0.3096)

## Design
- Heritage component: `property_rights` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:NE.TRD.GNFS.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `116.72306047291106` over `42` countries.
- Low-market mean: `68.8312771904438` over `41` countries.
- Difference, high minus low: `47.89178328246726`.
- Welch p-value: `0.0003415094486226856`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `158`.
- Market-score coefficient, standardized score: `5.845873580455979`.
- Controlled p-value: `0.3095743830123222`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
