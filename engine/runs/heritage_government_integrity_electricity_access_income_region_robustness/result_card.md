# Result card — heritage_government_integrity_electricity_access_income_region_robustness

**Verdict:** PARTIAL — controlled coefficient not decisive (coef=-1.565, p=0.261)

## Design
- Heritage component: `government_integrity` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:EG.ELC.ACCS.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `99.46666666666667` over `45` countries.
- Low-market mean: `71.73333333333332` over `45` countries.
- Difference, high minus low: `27.73333333333335`.
- Welch p-value: `4.2947648401578667e-08`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `173`.
- Market-score coefficient, standardized score: `-1.5651240053965947`.
- Controlled p-value: `0.26095593666810635`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
