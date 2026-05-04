# Result card — heritage_business_freedom_employment_rate_income_region_robustness

**Verdict:** PARTIAL — controlled coefficient not decisive (coef=1.837, p=0.3218)

## Design
- Heritage component: `business_freedom` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SL.EMP.TOTL.SP.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `59.44537209302325` over `43` countries.
- Low-market mean: `59.72727272727274` over `44` countries.
- Difference, high minus low: `-0.28190063424948875`.
- Welch p-value: `0.90513134854631`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `165`.
- Market-score coefficient, standardized score: `1.8374554078988934`.
- Controlled p-value: `0.32177748768540315`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
