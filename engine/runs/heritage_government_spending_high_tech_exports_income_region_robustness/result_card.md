# Result card — heritage_government_spending_high_tech_exports_income_region_robustness

**Verdict:** PARTIAL — controlled coefficient not decisive (coef=1.139, p=0.334)

## Design
- Heritage component: `government_spending` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:TX.VAL.TECH.MF.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `9.889659367063754` over `40` countries.
- Low-market mean: `16.005184423773176` over `40` countries.
- Difference, high minus low: `-6.115525056709423`.
- Welch p-value: `0.04077594034206938`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `159`.
- Market-score coefficient, standardized score: `1.1389369785796464`.
- Controlled p-value: `0.33397521361477456`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
