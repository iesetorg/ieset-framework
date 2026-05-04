# Result card — heritage_monetary_freedom_electricity_access_income_region_robustness

**Verdict:** PARTIAL — controlled coefficient not decisive (coef=-1.399, p=0.1626)

## Design
- Heritage component: `monetary_freedom` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:EG.ELC.ACCS.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `93.45681818181816` over `44` countries.
- Low-market mean: `79.11136363636363` over `44` countries.
- Difference, high minus low: `14.34545454545453`.
- Welch p-value: `0.002899018680406241`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `169`.
- Market-score coefficient, standardized score: `-1.399252872677674`.
- Controlled p-value: `0.16258033737446692`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
