# Result card — heritage_labor_freedom_employment_rate_income_region_robustness

**Verdict:** PARTIAL — controlled coefficient not decisive (coef=1.05, p=0.3422)

## Design
- Heritage component: `labor_freedom` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SL.EMP.TOTL.SP.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `57.77547727272727` over `44` countries.
- Low-market mean: `55.849441860465134` over `43` countries.
- Difference, high minus low: `1.926035412262138`.
- Welch p-value: `0.464966932986279`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `165`.
- Market-score coefficient, standardized score: `1.050046898263558`.
- Controlled p-value: `0.34219205120323093`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
