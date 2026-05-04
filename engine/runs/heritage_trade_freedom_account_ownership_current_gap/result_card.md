# Result card — heritage_trade_freedom_account_ownership_current_gap

**Verdict:** SUPPORTED — top-vs-bottom gap has expected sign + and Welch p=2.162e-11

## Design
- Heritage component: `trade_freedom` using release year `2024`.
- Comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:FX.OWN.TOTL.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `89.9588161506619` over `44` countries.
- Low-market mean: `57.93451478946118` over `36` countries.
- Difference, high minus low: `32.02430136120072`.
- Welch p-value: `2.162381805656254e-11`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
