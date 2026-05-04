# Result card — heritage_judicial_effectiveness_investment_share_income_region_robustness

**Verdict:** PARTIAL — controlled coefficient not decisive (coef=-0.08458, p=0.9175)

## Design
- Heritage component: `judicial_effectiveness` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:NE.GDI.TOTL.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `22.717349386706505` over `41` countries.
- Low-market mean: `20.784199583541323` over `40` countries.
- Difference, high minus low: `1.9331498031651826`.
- Welch p-value: `0.29239265113396895`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `157`.
- Market-score coefficient, standardized score: `-0.08457513430830943`.
- Controlled p-value: `0.9174755722037804`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
