# Result card — heritage_investment_freedom_account_ownership_income_region_robustness

**Verdict:** PARTIAL — controlled coefficient not decisive (coef=-1.198, p=0.4153)

## Design
- Heritage component: `investment_freedom` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:FX.OWN.TOTL.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `88.81881445013771` over `34` countries.
- Low-market mean: `60.782384504567425` over `38` countries.
- Difference, high minus low: `28.036429945570283`.
- Welch p-value: `4.320939098123335e-09`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `135`.
- Market-score coefficient, standardized score: `-1.1975304930117636`.
- Controlled p-value: `0.415272089017815`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
