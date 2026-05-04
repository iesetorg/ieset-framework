# Result card — heritage_government_spending_trade_openness_income_region_robustness

**Verdict:** PARTIAL — controlled coefficient not decisive (coef=1.724, p=0.7234)

## Design
- Heritage component: `government_spending` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:NE.TRD.GNFS.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `66.25219145160206` over `39` countries.
- Low-market mean: `112.46033484621374` over `39` countries.
- Difference, high minus low: `-46.20814339461168`.
- Welch p-value: `0.000801833921471484`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `154`.
- Market-score coefficient, standardized score: `1.724336349122962`.
- Controlled p-value: `0.7234162526874914`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
