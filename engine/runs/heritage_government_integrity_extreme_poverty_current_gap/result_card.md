# Result card — heritage_government_integrity_extreme_poverty_current_gap

**Verdict:** SUPPORTED — top-vs-bottom gap has expected sign - and Welch p=9.014e-06

## Design
- Heritage component: `government_integrity` using release year `2024`.
- Comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SI.POV.DDAY` latest available country observation since `2018`.

## Estimate
- High-market mean: `0.5272727272727273` over `33` countries.
- Low-market mean: `25.645454545454545` over `33` countries.
- Difference, high minus low: `-25.118181818181817`.
- Welch p-value: `9.013818400115915e-06`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
