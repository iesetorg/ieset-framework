# Result card — heritage_government_integrity_tertiary_enrollment_current_gap

**Verdict:** SUPPORTED — top-vs-bottom gap has expected sign + and Welch p=4.849e-13

## Design
- Heritage component: `government_integrity` using release year `2024`.
- Comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SE.TER.ENRR` latest available country observation since `2018`.

## Estimate
- High-market mean: `74.18763543493486` over `38` countries.
- Low-market mean: `28.10007640031204` over `37` countries.
- Difference, high minus low: `46.08755903462282`.
- Welch p-value: `4.849178346534861e-13`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
