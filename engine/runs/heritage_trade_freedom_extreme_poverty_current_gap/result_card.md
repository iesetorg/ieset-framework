# Result card — heritage_trade_freedom_extreme_poverty_current_gap

**Verdict:** SUPPORTED — top-vs-bottom gap has expected sign - and Welch p=8.095e-07

## Design
- Heritage component: `trade_freedom` using release year `2024`.
- Comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SI.POV.DDAY` latest available country observation since `2018`.

## Estimate
- High-market mean: `0.9857142857142859` over `42` countries.
- Low-market mean: `27.703125` over `32` countries.
- Difference, high minus low: `-26.717410714285712`.
- Welch p-value: `8.094714387496073e-07`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
