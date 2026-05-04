# Result card — heritage_economic_freedom_under5_mortality_current_gap

**Verdict:** SUPPORTED — top-vs-bottom gap has expected sign - and Welch p=2.12e-11

## Design
- Heritage component: `overall_score` using release year `2024`.
- Comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SH.DYN.MORT` latest available country observation since `2018`.

## Estimate
- High-market mean: `6.072727272727272` over `44` countries.
- Low-market mean: `41.87500000000001` over `44` countries.
- Difference, high minus low: `-35.80227272727274`.
- Welch p-value: `2.120214312623657e-11`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
