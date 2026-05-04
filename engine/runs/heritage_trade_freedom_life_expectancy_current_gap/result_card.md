# Result card — heritage_trade_freedom_life_expectancy_current_gap

**Verdict:** SUPPORTED — top-vs-bottom gap has expected sign + and Welch p=3.637e-16

## Design
- Heritage component: `trade_freedom` using release year `2024`.
- Comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SP.DYN.LE00.IN` latest available country observation since `2018`.

## Estimate
- High-market mean: `79.77882974653276` over `51` countries.
- Low-market mean: `68.5790909090909` over `44` countries.
- Difference, high minus low: `11.19973883744187`.
- Welch p-value: `3.6367083552208003e-16`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
