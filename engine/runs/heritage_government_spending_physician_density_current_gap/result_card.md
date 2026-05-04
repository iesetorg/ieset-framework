# Result card — heritage_government_spending_physician_density_current_gap

**Verdict:** REFUTED — top-vs-bottom gap has opposite sign and Welch p=2.48e-13

## Design
- Heritage component: `government_spending` using release year `2024`.
- Comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SH.MED.PHYS.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `0.7257142857142856` over `42` countries.
- Low-market mean: `3.498547619047619` over `42` countries.
- Difference, high minus low: `-2.7728333333333333`.
- Welch p-value: `2.48037439391769e-13`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
