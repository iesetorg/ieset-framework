# Result card — heritage_financial_freedom_physician_density_income_region_robustness

**Verdict:** PARTIAL — controlled coefficient not decisive (coef=-0.08561, p=0.373)

## Design
- Heritage component: `financial_freedom` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SH.MED.PHYS.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `3.116290322580645` over `62` countries.
- Low-market mean: `1.1977272727272728` over `66` countries.
- Difference, high minus low: `1.9185630498533723`.
- Welch p-value: `1.737355491207626e-10`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `163`.
- Market-score coefficient, standardized score: `-0.08560762903711414`.
- Controlled p-value: `0.37298184384938415`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
