# Result card — heritage_trade_freedom_inflation_rate_income_region_robustness

**Verdict:** SUPPORTED — controlled market-score coefficient has expected sign - and p=0.001174

## Design
- Heritage component: `trade_freedom` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:FP.CPI.TOTL.ZG` latest available country observation since `2018`.

## Estimate
- High-market mean: `2.387497420114923` over `50` countries.
- Low-market mean: `17.571371401299537` over `42` countries.
- Difference, high minus low: `-15.183873981184615`.
- Welch p-value: `0.021890825814977786`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `168`.
- Market-score coefficient, standardized score: `-7.437901930773871`.
- Controlled p-value: `0.0011739096163154823`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
