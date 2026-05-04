# Result card — heritage_investment_freedom_under5_mortality_income_region_robustness

**Verdict:** PARTIAL — controlled coefficient not decisive (coef=-0.7226, p=0.5933)

## Design
- Heritage component: `investment_freedom` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SH.DYN.MORT` latest available country observation since `2018`.

## Estimate
- High-market mean: `9.015254237288135` over `59` countries.
- Low-market mean: `34.82666666666666` over `45` countries.
- Difference, high minus low: `-25.811412429378528`.
- Welch p-value: `4.755913919562112e-08`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `170`.
- Market-score coefficient, standardized score: `-0.7226087962871715`.
- Controlled p-value: `0.5932691114399394`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
