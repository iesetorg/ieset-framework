# Result card — heritage_trade_freedom_physician_density_income_region_robustness

**Verdict:** SUPPORTED — controlled market-score coefficient has expected sign + and p=0.09301

## Design
- Heritage component: `trade_freedom` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SH.MED.PHYS.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `3.619957446808511` over `47` countries.
- Low-market mean: `0.7793333333333333` over `42` countries.
- Difference, high minus low: `2.8406241134751777`.
- Welch p-value: `2.000953487330163e-17`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `164`.
- Market-score coefficient, standardized score: `0.16538895640770646`.
- Controlled p-value: `0.09300914041083183`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
