# Result card — heritage_economic_freedom_electricity_access_current_gap

**Verdict:** SUPPORTED — top-vs-bottom gap has expected sign + and Welch p=9.711e-08

## Design
- Heritage component: `overall_score` using release year `2024`.
- Comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:EG.ELC.ACCS.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `99.40227272727272` over `44` countries.
- Low-market mean: `69.5909090909091` over `44` countries.
- Difference, high minus low: `29.811363636363623`.
- Welch p-value: `9.710903949742486e-08`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
