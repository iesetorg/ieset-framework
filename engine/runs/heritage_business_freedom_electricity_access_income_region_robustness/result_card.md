# Result card — heritage_business_freedom_electricity_access_income_region_robustness

**Verdict:** SUPPORTED — controlled market-score coefficient has expected sign + and p=4.061e-05

## Design
- Heritage component: `business_freedom` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:EG.ELC.ACCS.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `99.96136363636364` over `44` countries.
- Low-market mean: `56.63863636363636` over `44` countries.
- Difference, high minus low: `43.322727272727285`.
- Welch p-value: `1.0430754091472557e-13`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `169`.
- Market-score coefficient, standardized score: `7.985408864866102`.
- Controlled p-value: `4.061086558188218e-05`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
