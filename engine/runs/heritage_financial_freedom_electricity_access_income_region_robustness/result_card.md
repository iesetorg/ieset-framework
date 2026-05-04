# Result card — heritage_financial_freedom_electricity_access_income_region_robustness

**Verdict:** PARTIAL — controlled coefficient not decisive (coef=-1.237, p=0.3415)

## Design
- Heritage component: `financial_freedom` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:EG.ELC.ACCS.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `99.21230769230769` over `65` countries.
- Low-market mean: `78.32045454545455` over `44` countries.
- Difference, high minus low: `20.891853146853137`.
- Welch p-value: `1.4798134757875248e-05`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `169`.
- Market-score coefficient, standardized score: `-1.2367454569718965`.
- Controlled p-value: `0.34154645394168814`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
