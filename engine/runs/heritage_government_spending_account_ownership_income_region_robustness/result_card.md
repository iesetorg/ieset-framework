# Result card — heritage_government_spending_account_ownership_income_region_robustness

**Verdict:** REFUTED — controlled market-score coefficient has opposite sign and p=8.658e-05

## Design
- Heritage component: `government_spending` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:FX.OWN.TOTL.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `53.45774581812141` over `34` countries.
- Low-market mean: `93.02735652325623` over `34` countries.
- Difference, high minus low: `-39.56961070513482`.
- Welch p-value: `8.136109943277555e-13`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `135`.
- Market-score coefficient, standardized score: `-5.942774617693623`.
- Controlled p-value: `8.658205011302441e-05`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
