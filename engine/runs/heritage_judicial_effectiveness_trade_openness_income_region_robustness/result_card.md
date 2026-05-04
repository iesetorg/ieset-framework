# Result card — heritage_judicial_effectiveness_trade_openness_income_region_robustness

**Verdict:** PARTIAL — controlled coefficient not decisive (coef=1.541, p=0.761)

## Design
- Heritage component: `judicial_effectiveness` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:NE.TRD.GNFS.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `107.97126567682471` over `42` countries.
- Low-market mean: `74.23479876826961` over `41` countries.
- Difference, high minus low: `33.7364669085551`.
- Welch p-value: `0.0050810775168412155`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `158`.
- Market-score coefficient, standardized score: `1.540987606024157`.
- Controlled p-value: `0.7609823767694486`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
