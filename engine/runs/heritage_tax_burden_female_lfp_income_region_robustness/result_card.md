# Result card — heritage_tax_burden_female_lfp_income_region_robustness

**Verdict:** PARTIAL — controlled coefficient not decisive (coef=-0.03732, p=0.9727)

## Design
- Heritage component: `tax_burden` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SL.TLF.CACT.FE.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `50.0026511627907` over `43` countries.
- Low-market mean: `55.10830232558139` over `43` countries.
- Difference, high minus low: `-5.105651162790693`.
- Welch p-value: `0.0620373289798247`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `166`.
- Market-score coefficient, standardized score: `-0.037321809739709146`.
- Controlled p-value: `0.9727126974822742`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
