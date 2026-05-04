# Result card — heritage_business_freedom_life_expectancy_current_gap

**Verdict:** SUPPORTED — top-vs-bottom gap has expected sign + and Welch p=1.912e-25

## Design
- Heritage component: `business_freedom` using release year `2024`.
- Comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SP.DYN.LE00.IN` latest available country observation since `2018`.

## Estimate
- High-market mean: `81.0315792682927` over `44` countries.
- Low-market mean: `65.74381818181816` over `44` countries.
- Difference, high minus low: `15.287761086474546`.
- Welch p-value: `1.911806154299994e-25`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
