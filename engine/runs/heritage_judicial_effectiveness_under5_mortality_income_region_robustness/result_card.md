# Result card — heritage_judicial_effectiveness_under5_mortality_income_region_robustness

**Verdict:** SUPPORTED — controlled market-score coefficient has expected sign - and p=0.0374

## Design
- Heritage component: `judicial_effectiveness` using release year `2024`.
- Design: `ols_income_region`.
- Uncontrolled comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SH.DYN.MORT` latest available country observation since `2018`.

## Estimate
- High-market mean: `6.930434782608694` over `46` countries.
- Low-market mean: `37.97555555555556` over `45` countries.
- Difference, high minus low: `-31.045120772946866`.
- Welch p-value: `4.2724393132015177e-10`.

## Controlled Robustness
- Controls: `['log_gdp_pc_ppp_control']` plus categorical `['region']`.
- Controlled OLS n: `174`.
- Market-score coefficient, standardized score: `-2.7970257435525223`.
- Controlled p-value: `0.03739980439534977`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
