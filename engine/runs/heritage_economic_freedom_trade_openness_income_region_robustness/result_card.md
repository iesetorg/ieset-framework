# Result card — heritage_economic_freedom_trade_openness_income_region_robustness

**Verdict:** SUPPORTED — controlled market-score coefficient has expected sign + and p=0.0008464

## Design
- Heritage component: `overall_score` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:NE.TRD.GNFS.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `116.21528539141033` over `39` countries.
- Low-market mean: `61.8362443844171` over `40` countries.
- Difference, high minus low: `54.37904100699323`.
- Welch p-value: `6.58811430344145e-05`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `154`.
- Market-score coefficient, standardized score: `19.488735570815873`.
- Controlled p-value: `0.0008464326306023547`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
