# Result card — heritage_government_spending_investment_share_income_region_robustness

**Verdict:** PARTIAL — controlled coefficient not decisive (coef=0.1142, p=0.8821)

## Design
- Heritage component: `government_spending` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:NE.GDI.TOTL.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `21.73938458434515` over `39` countries.
- Low-market mean: `23.25611041703969` over `39` countries.
- Difference, high minus low: `-1.51672583269454`.
- Welch p-value: `0.4226602245023442`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `153`.
- Market-score coefficient, standardized score: `0.11415205976970544`.
- Controlled p-value: `0.8820990094605776`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
