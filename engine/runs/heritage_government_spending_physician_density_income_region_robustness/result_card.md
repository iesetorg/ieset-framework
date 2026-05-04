# Result card — heritage_government_spending_physician_density_income_region_robustness

**Verdict:** REFUTED — controlled market-score coefficient has opposite sign and p=0.05096

## Design
- Heritage component: `government_spending` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SH.MED.PHYS.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `0.7257142857142856` over `42` countries.
- Low-market mean: `3.498547619047619` over `42` countries.
- Difference, high minus low: `-2.7728333333333333`.
- Welch p-value: `2.48037439391769e-13`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `163`.
- Market-score coefficient, standardized score: `-0.18138631128031205`.
- Controlled p-value: `0.05095605102360914`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
