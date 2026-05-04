# Result card — heritage_investment_freedom_physician_density_income_region_robustness

**Verdict:** PARTIAL — controlled coefficient not decisive (coef=-0.1026, p=0.2822)

## Design
- Heritage component: `investment_freedom` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SH.MED.PHYS.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `3.227649122807018` over `57` countries.
- Low-market mean: `1.308875` over `56` countries.
- Difference, high minus low: `1.9187741228070179`.
- Welch p-value: `1.1237657284655545e-09`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `163`.
- Market-score coefficient, standardized score: `-0.10261718915252643`.
- Controlled p-value: `0.282218872269794`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
