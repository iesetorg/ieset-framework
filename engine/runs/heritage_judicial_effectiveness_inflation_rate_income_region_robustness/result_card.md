# Result card — heritage_judicial_effectiveness_inflation_rate_income_region_robustness

**Verdict:** PARTIAL — controlled coefficient not decisive (coef=-3.31, p=0.1487)

## Design
- Heritage component: `judicial_effectiveness` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:FP.CPI.TOTL.ZG` latest available country observation since `2018`.

## Estimate
- High-market mean: `2.4406990197571417` over `43` countries.
- Low-market mean: `14.795587437567281` over `43` countries.
- Difference, high minus low: `-12.35488841781014`.
- Welch p-value: `0.005434956999971225`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `171`.
- Market-score coefficient, standardized score: `-3.3104103336583153`.
- Controlled p-value: `0.14869943408085642`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
