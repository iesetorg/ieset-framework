# Result card — heritage_judicial_effectiveness_physician_density_income_region_robustness

**Verdict:** SUPPORTED — controlled market-score coefficient has expected sign + and p=0.09042

## Design
- Heritage component: `judicial_effectiveness` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SH.MED.PHYS.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `3.41653488372093` over `43` countries.
- Low-market mean: `1.0942325581395351` over `43` countries.
- Difference, high minus low: `2.3223023255813953`.
- Welch p-value: `4.913173115714987e-10`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `166`.
- Market-score coefficient, standardized score: `0.16172280076824777`.
- Controlled p-value: `0.09041944926482469`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
