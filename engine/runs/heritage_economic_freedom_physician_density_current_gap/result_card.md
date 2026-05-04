# Result card — heritage_economic_freedom_physician_density_current_gap

**Verdict:** SUPPORTED — top-vs-bottom gap has expected sign + and Welch p=8.619e-09

## Design
- Heritage component: `overall_score` using release year `2024`.
- Comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SH.MED.PHYS.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `3.523404761904762` over `42` countries.
- Low-market mean: `1.2442142857142857` over `42` countries.
- Difference, high minus low: `2.279190476190476`.
- Welch p-value: `8.619214557637905e-09`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
