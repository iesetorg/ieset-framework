# Result card — heritage_judicial_effectiveness_tertiary_enrollment_current_gap

**Verdict:** SUPPORTED — top-vs-bottom gap has expected sign + and Welch p=9.412e-10

## Design
- Heritage component: `judicial_effectiveness` using release year `2024`.
- Comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SE.TER.ENRR` latest available country observation since `2018`.

## Estimate
- High-market mean: `73.58339515683264` over `37` countries.
- Low-market mean: `32.94298597815319` over `37` countries.
- Difference, high minus low: `40.64040917867945`.
- Welch p-value: `9.411779235292714e-10`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
