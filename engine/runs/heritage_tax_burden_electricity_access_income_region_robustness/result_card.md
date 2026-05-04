# Result card — heritage_tax_burden_electricity_access_income_region_robustness

**Verdict:** PARTIAL — controlled coefficient not decisive (coef=1.457, p=0.1656)

## Design
- Heritage component: `tax_burden` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:EG.ELC.ACCS.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `93.15227272727275` over `44` countries.
- Low-market mean: `88.66136363636362` over `44` countries.
- Difference, high minus low: `4.490909090909128`.
- Welch p-value: `0.2841584217510688`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `170`.
- Market-score coefficient, standardized score: `1.4572858671266757`.
- Controlled p-value: `0.16557703069375104`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
