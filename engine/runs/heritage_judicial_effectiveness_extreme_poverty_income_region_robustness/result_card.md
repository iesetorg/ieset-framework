# Result card — heritage_judicial_effectiveness_extreme_poverty_income_region_robustness

**Verdict:** REFUTED — controlled market-score coefficient has opposite sign and p=0.01413

## Design
- Heritage component: `judicial_effectiveness` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SI.POV.DDAY` latest available country observation since `2018`.

## Estimate
- High-market mean: `0.43030303030303035` over `33` countries.
- Low-market mean: `21.68235294117647` over `34` countries.
- Difference, high minus low: `-21.252049910873442`.
- Welch p-value: `1.840369490983718e-05`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `129`.
- Market-score coefficient, standardized score: `3.345069438584396`.
- Controlled p-value: `0.014133113334583567`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
