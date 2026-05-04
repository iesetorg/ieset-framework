# Result card — heritage_business_freedom_under5_mortality_income_region_robustness

**Verdict:** SUPPORTED — controlled market-score coefficient has expected sign - and p=5.89e-05

## Design
- Heritage component: `business_freedom` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SH.DYN.MORT` latest available country observation since `2018`.

## Estimate
- High-market mean: `5.613636363636364` over `44` countries.
- Low-market mean: `54.72727272727272` over `44` countries.
- Difference, high minus low: `-49.11363636363635`.
- Welch p-value: `4.450017963419529e-16`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `170`.
- Market-score coefficient, standardized score: `-8.218156991735492`.
- Controlled p-value: `5.8899810753922595e-05`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
