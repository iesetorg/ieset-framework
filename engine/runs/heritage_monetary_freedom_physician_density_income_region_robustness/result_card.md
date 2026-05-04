# Result card — heritage_monetary_freedom_physician_density_income_region_robustness

**Verdict:** PARTIAL — controlled coefficient not decisive (coef=-0.05532, p=0.4603)

## Design
- Heritage component: `monetary_freedom` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SH.MED.PHYS.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `2.328690476190476` over `42` countries.
- Low-market mean: `1.8289767441860465` over `43` countries.
- Difference, high minus low: `0.49971373200442937`.
- Welch p-value: `0.21784707180908505`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `163`.
- Market-score coefficient, standardized score: `-0.05532122679927292`.
- Controlled p-value: `0.4602871606608093`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
