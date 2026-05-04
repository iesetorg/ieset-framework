# Result card — heritage_trade_freedom_physician_density_current_gap

**Verdict:** SUPPORTED — top-vs-bottom gap has expected sign + and Welch p=2.001e-17

## Design
- Heritage component: `trade_freedom` using release year `2024`.
- Comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SH.MED.PHYS.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `3.619957446808511` over `47` countries.
- Low-market mean: `0.7793333333333333` over `42` countries.
- Difference, high minus low: `2.8406241134751777`.
- Welch p-value: `2.000953487330163e-17`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
