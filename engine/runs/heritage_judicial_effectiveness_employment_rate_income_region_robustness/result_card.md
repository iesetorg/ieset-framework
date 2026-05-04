# Result card — heritage_judicial_effectiveness_employment_rate_income_region_robustness

**Verdict:** PARTIAL — controlled coefficient not decisive (coef=0.4339, p=0.7281)

## Design
- Heritage component: `judicial_effectiveness` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SL.EMP.TOTL.SP.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `58.30993181818182` over `44` countries.
- Low-market mean: `54.33138636363637` over `44` countries.
- Difference, high minus low: `3.978545454545454`.
- Welch p-value: `0.08894850086988391`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `169`.
- Market-score coefficient, standardized score: `0.43388891910009086`.
- Controlled p-value: `0.7280995244995744`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
