# Result card — heritage_judicial_effectiveness_electricity_access_current_gap

**Verdict:** SUPPORTED — top-vs-bottom gap has expected sign + and Welch p=3.471e-07

## Design
- Heritage component: `judicial_effectiveness` using release year `2024`.
- Comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:EG.ELC.ACCS.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `99.6688888888889` over `45` countries.
- Low-market mean: `75.13111111111111` over `45` countries.
- Difference, high minus low: `24.53777777777779`.
- Welch p-value: `3.471448580359794e-07`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
