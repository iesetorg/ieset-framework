# Result card — heritage_labor_freedom_trade_openness_income_region_robustness

**Verdict:** PARTIAL — controlled coefficient not decisive (coef=4.555, p=0.3214)

## Design
- Heritage component: `labor_freedom` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:NE.TRD.GNFS.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `111.83630621369316` over `39` countries.
- Low-market mean: `72.26192681608197` over `39` countries.
- Difference, high minus low: `39.574379397611196`.
- Welch p-value: `0.0016874415250390925`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `154`.
- Market-score coefficient, standardized score: `4.555226512934438`.
- Controlled p-value: `0.3213516751039489`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
