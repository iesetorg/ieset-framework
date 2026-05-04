# Result card — heritage_monetary_freedom_account_ownership_income_region_robustness

**Verdict:** PARTIAL — controlled coefficient not decisive (coef=0.4389, p=0.6968)

## Design
- Heritage component: `monetary_freedom` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:FX.OWN.TOTL.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `78.091147086175` over `34` countries.
- Low-market mean: `63.32432645424009` over `34` countries.
- Difference, high minus low: `14.766820631934912`.
- Welch p-value: `0.0038290260870529466`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `135`.
- Market-score coefficient, standardized score: `0.4388532735286933`.
- Controlled p-value: `0.6968031119104725`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
