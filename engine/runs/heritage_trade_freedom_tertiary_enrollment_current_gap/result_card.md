# Result card — heritage_trade_freedom_tertiary_enrollment_current_gap

**Verdict:** SUPPORTED — top-vs-bottom gap has expected sign + and Welch p=5.027e-12

## Design
- Heritage component: `trade_freedom` using release year `2024`.
- Comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SE.TER.ENRR` latest available country observation since `2018`.

## Estimate
- High-market mean: `70.90787819223105` over `49` countries.
- Low-market mean: `26.212378586645453` over `37` countries.
- Difference, high minus low: `44.695499605585596`.
- Welch p-value: `5.026845931283015e-12`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
