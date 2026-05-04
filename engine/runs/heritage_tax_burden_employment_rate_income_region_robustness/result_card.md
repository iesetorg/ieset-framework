# Result card — heritage_tax_burden_employment_rate_income_region_robustness

**Verdict:** PARTIAL — controlled coefficient not decisive (coef=0.8483, p=0.3826)

## Design
- Heritage component: `tax_burden` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SL.EMP.TOTL.SP.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `58.48637209302326` over `43` countries.
- Low-market mean: `57.954069767441865` over `43` countries.
- Difference, high minus low: `0.5323023255813979`.
- Welch p-value: `0.8256636442370264`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `166`.
- Market-score coefficient, standardized score: `0.8483211555337286`.
- Controlled p-value: `0.3825958497973794`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
