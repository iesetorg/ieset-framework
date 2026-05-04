# Result card — heritage_economic_freedom_employment_rate_income_region_robustness

**Verdict:** SUPPORTED — controlled market-score coefficient has expected sign + and p=0.004573

## Design
- Heritage component: `overall_score` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SL.EMP.TOTL.SP.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `60.42444186046512` over `43` countries.
- Low-market mean: `56.799372093023266` over `43` countries.
- Difference, high minus low: `3.6250697674418575`.
- Welch p-value: `0.10503283742676432`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `165`.
- Market-score coefficient, standardized score: `3.89144237657824`.
- Controlled p-value: `0.004573201819173577`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
