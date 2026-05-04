# Result card — heritage_labor_freedom_tertiary_enrollment_current_gap

**Verdict:** SUPPORTED — top-vs-bottom gap has expected sign + and Welch p=4.795e-08

## Design
- Heritage component: `labor_freedom` using release year `2024`.
- Comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SE.TER.ENRR` latest available country observation since `2018`.

## Estimate
- High-market mean: `69.03701669528006` over `36` countries.
- Low-market mean: `32.42308899116168` over `36` countries.
- Difference, high minus low: `36.61392770411838`.
- Welch p-value: `4.794684454376984e-08`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
