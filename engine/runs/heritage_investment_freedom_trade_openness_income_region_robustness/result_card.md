# Result card — heritage_investment_freedom_trade_openness_income_region_robustness

**Verdict:** SUPPORTED — controlled market-score coefficient has expected sign + and p=0.01518

## Design
- Heritage component: `investment_freedom` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:NE.TRD.GNFS.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `109.7071681204355` over `56` countries.
- Low-market mean: `72.47015980279828` over `53` countries.
- Difference, high minus low: `37.23700831763722`.
- Welch p-value: `0.0005285453981741299`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `154`.
- Market-score coefficient, standardized score: `12.167893591303457`.
- Controlled p-value: `0.015176527716173085`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
