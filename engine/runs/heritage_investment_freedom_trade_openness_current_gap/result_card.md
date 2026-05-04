# Result card — heritage_investment_freedom_trade_openness_current_gap

**Verdict:** SUPPORTED — top-vs-bottom gap has expected sign + and Welch p=0.0005285

## Design
- Heritage component: `investment_freedom` using release year `2024`.
- Comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:NE.TRD.GNFS.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `109.7071681204355` over `56` countries.
- Low-market mean: `72.47015980279828` over `53` countries.
- Difference, high minus low: `37.23700831763722`.
- Welch p-value: `0.0005285453981741299`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
