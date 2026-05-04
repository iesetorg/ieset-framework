# Result card — heritage_labor_freedom_electricity_access_income_region_robustness

**Verdict:** PARTIAL — controlled coefficient not decisive (coef=-1.894, p=0.1052)

## Design
- Heritage component: `labor_freedom` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:EG.ELC.ACCS.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `95.73555555555555` over `45` countries.
- Low-market mean: `76.80444444444444` over `45` countries.
- Difference, high minus low: `18.931111111111107`.
- Welch p-value: `5.647439201180503e-05`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `169`.
- Market-score coefficient, standardized score: `-1.8943284017542974`.
- Controlled p-value: `0.10516625968965661`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
