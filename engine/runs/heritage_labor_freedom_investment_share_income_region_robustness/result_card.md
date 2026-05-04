# Result card — heritage_labor_freedom_investment_share_income_region_robustness

**Verdict:** PARTIAL — controlled coefficient not decisive (coef=0.4104, p=0.5766)

## Design
- Heritage component: `labor_freedom` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:NE.GDI.TOTL.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `23.840486278281652` over `39` countries.
- Low-market mean: `23.438309986790042` over `39` countries.
- Difference, high minus low: `0.40217629149161027`.
- Welch p-value: `0.8218455337905164`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `153`.
- Market-score coefficient, standardized score: `0.4103877160655945`.
- Controlled p-value: `0.5765666020321732`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
