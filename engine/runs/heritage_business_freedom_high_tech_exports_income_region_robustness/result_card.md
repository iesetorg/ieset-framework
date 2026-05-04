# Result card — heritage_business_freedom_high_tech_exports_income_region_robustness

**Verdict:** SUPPORTED — controlled market-score coefficient has expected sign + and p=0.03492

## Design
- Heritage component: `business_freedom` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:TX.VAL.TECH.MF.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `20.351088046398075` over `40` countries.
- Low-market mean: `3.9860088170379697` over `40` countries.
- Difference, high minus low: `16.365079229360106`.
- Welch p-value: `1.0509131382375855e-08`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `159`.
- Market-score coefficient, standardized score: `4.154957996744304`.
- Controlled p-value: `0.03491976734112368`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
