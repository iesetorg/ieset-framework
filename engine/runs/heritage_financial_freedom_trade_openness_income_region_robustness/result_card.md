# Result card — heritage_financial_freedom_trade_openness_income_region_robustness

**Verdict:** PARTIAL — controlled coefficient not decisive (coef=6.828, p=0.1817)

## Design
- Heritage component: `financial_freedom` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:NE.TRD.GNFS.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `106.68846478554299` over `63` countries.
- Low-market mean: `69.57968000577453` over `58` countries.
- Difference, high minus low: `37.108784779768456`.
- Welch p-value: `8.628760774992288e-05`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `154`.
- Market-score coefficient, standardized score: `6.827991957513035`.
- Controlled p-value: `0.18170939849948786`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
