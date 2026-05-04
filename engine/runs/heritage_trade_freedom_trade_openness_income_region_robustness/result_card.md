# Result card — heritage_trade_freedom_trade_openness_income_region_robustness

**Verdict:** SUPPORTED — controlled market-score coefficient has expected sign + and p=0.09715

## Design
- Heritage component: `trade_freedom` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:NE.TRD.GNFS.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `123.32242586051883` over `50` countries.
- Low-market mean: `63.938818056722496` over `40` countries.
- Difference, high minus low: `59.38360780379634`.
- Welch p-value: `9.880572800984262e-07`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `155`.
- Market-score coefficient, standardized score: `8.62675341981374`.
- Controlled p-value: `0.0971467953064559`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
