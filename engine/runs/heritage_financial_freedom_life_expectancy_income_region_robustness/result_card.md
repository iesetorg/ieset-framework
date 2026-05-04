# Result card — heritage_financial_freedom_life_expectancy_income_region_robustness

**Verdict:** SUPPORTED — controlled market-score coefficient has expected sign + and p=0.0005955

## Design
- Heritage component: `financial_freedom` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SP.DYN.LE00.IN` latest available country observation since `2018`.

## Estimate
- High-market mean: `79.32304052532832` over `65` countries.
- Low-market mean: `70.47817669376695` over `45` countries.
- Difference, high minus low: `8.84486383156137`.
- Welch p-value: `1.4352239198954978e-13`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `170`.
- Market-score coefficient, standardized score: `1.0928146440227098`.
- Controlled p-value: `0.0005955102388095042`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
