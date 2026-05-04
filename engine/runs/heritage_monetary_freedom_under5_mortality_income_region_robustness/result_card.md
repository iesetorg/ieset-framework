# Result card — heritage_monetary_freedom_under5_mortality_income_region_robustness

**Verdict:** PARTIAL — controlled coefficient not decisive (coef=0.1649, p=0.8758)

## Design
- Heritage component: `monetary_freedom` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SH.DYN.MORT` latest available country observation since `2018`.

## Estimate
- High-market mean: `18.204545454545453` over `44` countries.
- Low-market mean: `30.200000000000006` over `45` countries.
- Difference, high minus low: `-11.995454545454553`.
- Welch p-value: `0.01711603277926434`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `170`.
- Market-score coefficient, standardized score: `0.1649164795709471`.
- Controlled p-value: `0.8758265370472919`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
