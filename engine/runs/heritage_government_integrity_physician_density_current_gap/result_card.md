# Result card — heritage_government_integrity_physician_density_current_gap

**Verdict:** SUPPORTED — top-vs-bottom gap has expected sign + and Welch p=4.447e-17

## Design
- Heritage component: `government_integrity` using release year `2024`.
- Comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SH.MED.PHYS.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `3.624906976744187` over `43` countries.
- Low-market mean: `0.8367209302325583` over `43` countries.
- Difference, high minus low: `2.788186046511629`.
- Welch p-value: `4.446552676334834e-17`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
