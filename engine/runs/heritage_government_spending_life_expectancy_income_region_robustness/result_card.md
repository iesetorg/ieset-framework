# Result card — heritage_government_spending_life_expectancy_income_region_robustness

**Verdict:** REFUTED — controlled market-score coefficient has opposite sign and p=0.02111

## Design
- Heritage component: `government_spending` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SP.DYN.LE00.IN` latest available country observation since `2018`.

## Estimate
- High-market mean: `67.64175776053214` over `44` countries.
- Low-market mean: `78.8894756097561` over `44` countries.
- Difference, high minus low: `-11.24771784922396`.
- Welch p-value: `2.3081227114902224e-13`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `170`.
- Market-score coefficient, standardized score: `-0.6980941442174068`.
- Controlled p-value: `0.021114478622564145`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
