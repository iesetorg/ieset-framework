# Result card — heritage_monetary_freedom_investment_share_income_region_robustness

**Verdict:** SUPPORTED — controlled market-score coefficient has expected sign + and p=0.001012

## Design
- Heritage component: `monetary_freedom` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:NE.GDI.TOTL.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `23.317425581508715` over `39` countries.
- Low-market mean: `21.70947592656463` over `40` countries.
- Difference, high minus low: `1.6079496549440861`.
- Welch p-value: `0.34475685781125`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `153`.
- Market-score coefficient, standardized score: `1.964189628696369`.
- Controlled p-value: `0.0010124006706328133`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
