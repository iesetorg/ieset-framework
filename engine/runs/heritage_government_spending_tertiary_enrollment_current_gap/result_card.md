# Result card — heritage_government_spending_tertiary_enrollment_current_gap

**Verdict:** REFUTED — top-vs-bottom gap has opposite sign and Welch p=9.693e-09

## Design
- Heritage component: `government_spending` using release year `2024`.
- Comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SE.TER.ENRR` latest available country observation since `2018`.

## Estimate
- High-market mean: `27.48667523163536` over `36` countries.
- Low-market mean: `68.60609921865611` over `36` countries.
- Difference, high minus low: `-41.11942398702075`.
- Welch p-value: `9.692796481915311e-09`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
