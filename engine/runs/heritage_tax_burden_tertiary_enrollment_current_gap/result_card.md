# Result card — heritage_tax_burden_tertiary_enrollment_current_gap

**Verdict:** REFUTED — top-vs-bottom gap has opposite sign and Welch p=0.01966

## Design
- Heritage component: `tax_burden` using release year `2024`.
- Comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SE.TER.ENRR` latest available country observation since `2018`.

## Estimate
- High-market mean: `51.48786378926056` over `36` countries.
- Low-market mean: `68.03682166208006` over `36` countries.
- Difference, high minus low: `-16.5489578728195`.
- Welch p-value: `0.019664132281885204`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
