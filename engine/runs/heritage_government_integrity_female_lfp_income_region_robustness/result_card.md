# Result card — heritage_government_integrity_female_lfp_income_region_robustness

**Verdict:** SUPPORTED — controlled market-score coefficient has expected sign + and p=0.004862

## Design
- Heritage component: `government_integrity` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SL.TLF.CACT.FE.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `57.16336363636365` over `44` countries.
- Low-market mean: `47.198499999999996` over `44` countries.
- Difference, high minus low: `9.964863636363653`.
- Welch p-value: `0.007081408783908801`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `169`.
- Market-score coefficient, standardized score: `4.201406170460541`.
- Controlled p-value: `0.00486191250207149`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
