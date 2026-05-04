# Result card — heritage_government_spending_under5_mortality_income_region_robustness

**Verdict:** PARTIAL — controlled coefficient not decisive (coef=1.711, p=0.1799)

## Design
- Heritage component: `government_spending` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SH.DYN.MORT` latest available country observation since `2018`.

## Estimate
- High-market mean: `47.44772727272727` over `44` countries.
- Low-market mean: `9.422727272727274` over `44` countries.
- Difference, high minus low: `38.025`.
- Welch p-value: `2.2563797921964656e-11`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `170`.
- Market-score coefficient, standardized score: `1.7111581186478535`.
- Controlled p-value: `0.17991692820303115`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
