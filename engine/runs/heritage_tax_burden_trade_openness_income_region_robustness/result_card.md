# Result card — heritage_tax_burden_trade_openness_income_region_robustness

**Verdict:** SUPPORTED — controlled market-score coefficient has expected sign + and p=0.01898

## Design
- Heritage component: `tax_burden` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:NE.TRD.GNFS.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `103.07144445933764` over `40` countries.
- Low-market mean: `89.93737978911919` over `40` countries.
- Difference, high minus low: `13.13406467021845`.
- Welch p-value: `0.29818952862272513`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `155`.
- Market-score coefficient, standardized score: `9.582167977990146`.
- Controlled p-value: `0.018978656648703733`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
