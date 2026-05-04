# Result card — heritage_tax_burden_under5_mortality_income_region_robustness

**Verdict:** PARTIAL — controlled coefficient not decisive (coef=-0.3884, p=0.7236)

## Design
- Heritage component: `tax_burden` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SH.DYN.MORT` latest available country observation since `2018`.

## Estimate
- High-market mean: `17.759090909090908` over `44` countries.
- Low-market mean: `18.886363636363633` over `44` countries.
- Difference, high minus low: `-1.1272727272727252`.
- Welch p-value: `0.8110412359746894`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `171`.
- Market-score coefficient, standardized score: `-0.388446092510668`.
- Controlled p-value: `0.7236118210667951`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
