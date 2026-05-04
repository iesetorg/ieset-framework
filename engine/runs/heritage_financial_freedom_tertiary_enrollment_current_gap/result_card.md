# Result card — heritage_financial_freedom_tertiary_enrollment_current_gap

**Verdict:** SUPPORTED — top-vs-bottom gap has expected sign + and Welch p=6.468e-16

## Design
- Heritage component: `financial_freedom` using release year `2024`.
- Comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SE.TER.ENRR` latest available country observation since `2018`.

## Estimate
- High-market mean: `73.40470684598478` over `36` countries.
- Low-market mean: `27.900241690811878` over `47` countries.
- Difference, high minus low: `45.504465155172895`.
- Welch p-value: `6.467668190663822e-16`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
