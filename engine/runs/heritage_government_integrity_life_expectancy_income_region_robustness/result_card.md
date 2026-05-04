# Result card — heritage_government_integrity_life_expectancy_income_region_robustness

**Verdict:** SUPPORTED — controlled market-score coefficient has expected sign + and p=1.315e-06

## Design
- Heritage component: `government_integrity` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SP.DYN.LE00.IN` latest available country observation since `2018`.

## Estimate
- High-market mean: `80.12920813008131` over `45` countries.
- Low-market mean: `68.0498108401084` over `45` countries.
- Difference, high minus low: `12.079397289972903`.
- Welch p-value: `3.397098726748392e-19`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `174`.
- Market-score coefficient, standardized score: `1.6320814121543161`.
- Controlled p-value: `1.3152641059782835e-06`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
