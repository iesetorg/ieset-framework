# Result card — heritage_tax_burden_physician_density_income_region_robustness

**Verdict:** PARTIAL — controlled coefficient not decisive (coef=-0.09846, p=0.2114)

## Design
- Heritage component: `tax_burden` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SH.MED.PHYS.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `2.256452380952381` over `42` countries.
- Low-market mean: `2.9068139534883723` over `43` countries.
- Difference, high minus low: `-0.6503615725359913`.
- Welch p-value: `0.10871843105796439`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `163`.
- Market-score coefficient, standardized score: `-0.09845748374245934`.
- Controlled p-value: `0.21136776934761967`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
