# Result card — heritage_labor_freedom_physician_density_income_region_robustness

**Verdict:** PARTIAL — controlled coefficient not decisive (coef=-0.02446, p=0.7817)

## Design
- Heritage component: `labor_freedom` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SH.MED.PHYS.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `3.0882093023255814` over `43` countries.
- Low-market mean: `1.3059523809523812` over `42` countries.
- Difference, high minus low: `1.7822569213732002`.
- Welch p-value: `1.6422915086172862e-05`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `163`.
- Market-score coefficient, standardized score: `-0.02445809666612878`.
- Controlled p-value: `0.7816565588885724`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
