# Result card — heritage_government_integrity_electricity_access_current_gap

**Verdict:** SUPPORTED — top-vs-bottom gap has expected sign + and Welch p=4.295e-08

## Design
- Heritage component: `government_integrity` using release year `2024`.
- Comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:EG.ELC.ACCS.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `99.46666666666667` over `45` countries.
- Low-market mean: `71.73333333333332` over `45` countries.
- Difference, high minus low: `27.73333333333335`.
- Welch p-value: `4.2947648401578667e-08`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
