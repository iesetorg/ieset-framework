# Result card — heritage_investment_freedom_female_lfp_income_region_robustness

**Verdict:** PARTIAL — controlled coefficient not decisive (coef=1.373, p=0.2996)

## Design
- Heritage component: `investment_freedom` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SL.TLF.CACT.FE.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `54.864034482758626` over `58` countries.
- Low-market mean: `50.87227906976744` over `43` countries.
- Difference, high minus low: `3.991755412991189`.
- Welch p-value: `0.1978334483995254`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `165`.
- Market-score coefficient, standardized score: `1.373127758357167`.
- Controlled p-value: `0.29962029345924795`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
