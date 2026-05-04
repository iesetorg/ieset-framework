# Result card — heritage_tax_burden_inflation_rate_income_region_robustness

**Verdict:** PARTIAL — controlled coefficient not decisive (coef=-0.9108, p=0.6245)

## Design
- Heritage component: `tax_burden` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:FP.CPI.TOTL.ZG` latest available country observation since `2018`.

## Estimate
- High-market mean: `5.851955046322062` over `42` countries.
- Low-market mean: `8.261928284874202` over `42` countries.
- Difference, high minus low: `-2.4099732385521397`.
- Welch p-value: `0.6538688483322518`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `168`.
- Market-score coefficient, standardized score: `-0.9107823837528244`.
- Controlled p-value: `0.6244755545821606`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
