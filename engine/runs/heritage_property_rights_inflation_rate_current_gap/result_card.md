# Result card — heritage_property_rights_inflation_rate_current_gap

**Verdict:** SUPPORTED — top-vs-bottom gap has expected sign - and Welch p=0.01172

## Design
- Heritage component: `property_rights` using release year `2024`.
- Comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:FP.CPI.TOTL.ZG` latest available country observation since `2018`.

## Estimate
- High-market mean: `2.5944552750845427` over `43` countries.
- Low-market mean: `19.116861865322587` over `43` countries.
- Difference, high minus low: `-16.522406590238045`.
- Welch p-value: `0.011721885836021994`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
