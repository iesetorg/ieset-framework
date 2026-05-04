# Result card — heritage_monetary_freedom_private_consumption_pc_income_region_robustness

**Verdict:** PARTIAL — controlled coefficient not decisive (coef=555.7, p=0.2867)

## Design
- Heritage component: `monetary_freedom` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:NE.CON.PRVT.PC.KD` latest available country observation since `2018`.

## Estimate
- High-market mean: `12338.477553466773` over `37` countries.
- Low-market mean: `4005.557663034485` over `37` countries.
- Difference, high minus low: `8332.919890432288`.
- Welch p-value: `7.519463798627262e-05`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `147`.
- Market-score coefficient, standardized score: `555.69990789471`.
- Controlled p-value: `0.2867425876519486`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
