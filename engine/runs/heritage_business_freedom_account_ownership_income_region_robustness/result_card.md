# Result card — heritage_business_freedom_account_ownership_income_region_robustness

**Verdict:** SUPPORTED — controlled market-score coefficient has expected sign + and p=0.004837

## Design
- Heritage component: `business_freedom` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:FX.OWN.TOTL.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `95.01235649377463` over `35` countries.
- Low-market mean: `48.644010701709206` over `34` countries.
- Difference, high minus low: `46.368345792065426`.
- Welch p-value: `1.9522358313131707e-17`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `135`.
- Market-score coefficient, standardized score: `7.2913083474199745`.
- Controlled p-value: `0.00483719038356435`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
