# Result card — heritage_labor_freedom_account_ownership_income_region_robustness

**Verdict:** SUPPORTED — controlled market-score coefficient has expected sign + and p=0.04551

## Design
- Heritage component: `labor_freedom` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:FX.OWN.TOTL.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `90.90242704959736` over `35` countries.
- Low-market mean: `52.164659098769505` over `34` countries.
- Difference, high minus low: `38.73776795082786`.
- Welch p-value: `2.6812826125702935e-17`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `135`.
- Market-score coefficient, standardized score: `2.831552085625269`.
- Controlled p-value: `0.04550966419571762`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
