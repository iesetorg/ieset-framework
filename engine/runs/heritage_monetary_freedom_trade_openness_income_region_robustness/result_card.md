# Result card — heritage_monetary_freedom_trade_openness_income_region_robustness

**Verdict:** SUPPORTED — controlled market-score coefficient has expected sign + and p=0.07861

## Design
- Heritage component: `monetary_freedom` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:NE.TRD.GNFS.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `104.43969925673989` over `39` countries.
- Low-market mean: `75.89427034686646` over `40` countries.
- Difference, high minus low: `28.545428909873422`.
- Welch p-value: `0.01948256608318437`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `154`.
- Market-score coefficient, standardized score: `6.904468078019918`.
- Controlled p-value: `0.07861078220182943`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
