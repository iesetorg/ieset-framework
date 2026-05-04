# Result card — heritage_judicial_effectiveness_high_tech_exports_income_region_robustness

**Verdict:** SUPPORTED — controlled market-score coefficient has expected sign + and p=0.004948

## Design
- Heritage component: `judicial_effectiveness` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:TX.VAL.TECH.MF.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `20.24960035537118` over `41` countries.
- Low-market mean: `4.375113703754092` over `41` countries.
- Difference, high minus low: `15.874486651617087`.
- Welch p-value: `1.1947908549253258e-07`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `162`.
- Market-score coefficient, standardized score: `3.5116736479740838`.
- Controlled p-value: `0.004947667950561237`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
