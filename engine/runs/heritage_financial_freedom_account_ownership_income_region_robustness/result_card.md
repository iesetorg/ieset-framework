# Result card — heritage_financial_freedom_account_ownership_income_region_robustness

**Verdict:** PARTIAL — controlled coefficient not decisive (coef=1.116, p=0.4508)

## Design
- Heritage component: `financial_freedom` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:FX.OWN.TOTL.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `89.36828923305004` over `34` countries.
- Low-market mean: `56.24197188301568` over `42` countries.
- Difference, high minus low: `33.126317350034356`.
- Welch p-value: `6.430790394426701e-12`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `135`.
- Market-score coefficient, standardized score: `1.1156651954528805`.
- Controlled p-value: `0.45082487008725103`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
