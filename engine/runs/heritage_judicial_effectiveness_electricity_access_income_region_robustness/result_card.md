# Result card — heritage_judicial_effectiveness_electricity_access_income_region_robustness

**Verdict:** PARTIAL — controlled coefficient not decisive (coef=-0.8651, p=0.505)

## Design
- Heritage component: `judicial_effectiveness` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:EG.ELC.ACCS.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `99.6688888888889` over `45` countries.
- Low-market mean: `75.13111111111111` over `45` countries.
- Difference, high minus low: `24.53777777777779`.
- Welch p-value: `3.471448580359794e-07`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `173`.
- Market-score coefficient, standardized score: `-0.8650793280725356`.
- Controlled p-value: `0.5050130183311895`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
