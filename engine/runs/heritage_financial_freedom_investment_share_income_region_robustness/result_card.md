# Result card — heritage_financial_freedom_investment_share_income_region_robustness

**Verdict:** PARTIAL — controlled coefficient not decisive (coef=-0.03484, p=0.9649)

## Design
- Heritage component: `financial_freedom` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:NE.GDI.TOTL.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `23.370579001172008` over `63` countries.
- Low-market mean: `23.862026712059315` over `56` countries.
- Difference, high minus low: `-0.4914477108873072`.
- Welch p-value: `0.7449017648362916`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `153`.
- Market-score coefficient, standardized score: `-0.034840698664667734`.
- Controlled p-value: `0.9648568747114565`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
