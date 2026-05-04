# Result card — heritage_business_freedom_physician_density_income_region_robustness

**Verdict:** PARTIAL — controlled coefficient not decisive (coef=0.179, p=0.2284)

## Design
- Heritage component: `business_freedom` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SH.MED.PHYS.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `3.8008571428571436` over `42` countries.
- Low-market mean: `0.6489523809523808` over `42` countries.
- Difference, high minus low: `3.151904761904763`.
- Welch p-value: `3.047335009149734e-17`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `163`.
- Market-score coefficient, standardized score: `0.17900573934400965`.
- Controlled p-value: `0.22836505525419612`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
