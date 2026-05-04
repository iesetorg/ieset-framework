# Result card — heritage_government_integrity_trade_openness_current_gap

**Verdict:** SUPPORTED — top-vs-bottom gap has expected sign + and Welch p=0.0009128

## Design
- Heritage component: `government_integrity` using release year `2024`.
- Comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:NE.TRD.GNFS.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `112.8753662208614` over `41` countries.
- Low-market mean: `68.75279240320863` over `41` countries.
- Difference, high minus low: `44.122573817652764`.
- Welch p-value: `0.0009128059481494737`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
