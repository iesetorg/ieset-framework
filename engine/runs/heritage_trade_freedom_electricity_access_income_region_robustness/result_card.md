# Result card — heritage_trade_freedom_electricity_access_income_region_robustness

**Verdict:** PARTIAL — controlled coefficient not decisive (coef=-0.9576, p=0.4607)

## Design
- Heritage component: `trade_freedom` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:EG.ELC.ACCS.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `99.82600000000001` over `50` countries.
- Low-market mean: `71.91136363636363` over `44` countries.
- Difference, high minus low: `27.914636363636376`.
- Welch p-value: `7.134257320092994e-08`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `170`.
- Market-score coefficient, standardized score: `-0.9576464817484762`.
- Controlled p-value: `0.4607011930593461`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
