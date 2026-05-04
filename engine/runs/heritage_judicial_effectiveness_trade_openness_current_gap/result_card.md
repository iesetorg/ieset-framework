# Result card — heritage_judicial_effectiveness_trade_openness_current_gap

**Verdict:** SUPPORTED — top-vs-bottom gap has expected sign + and Welch p=0.005081

## Design
- Heritage component: `judicial_effectiveness` using release year `2024`.
- Comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:NE.TRD.GNFS.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `107.97126567682471` over `42` countries.
- Low-market mean: `74.23479876826961` over `41` countries.
- Difference, high minus low: `33.7364669085551`.
- Welch p-value: `0.0050810775168412155`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
