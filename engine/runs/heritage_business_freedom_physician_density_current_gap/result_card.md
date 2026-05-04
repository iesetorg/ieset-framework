# Result card — heritage_business_freedom_physician_density_current_gap

**Verdict:** SUPPORTED — top-vs-bottom gap has expected sign + and Welch p=3.047e-17

## Design
- Heritage component: `business_freedom` using release year `2024`.
- Comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SH.MED.PHYS.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `3.8008571428571436` over `42` countries.
- Low-market mean: `0.6489523809523808` over `42` countries.
- Difference, high minus low: `3.151904761904763`.
- Welch p-value: `3.047335009149734e-17`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
