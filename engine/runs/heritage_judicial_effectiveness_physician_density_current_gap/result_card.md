# Result card — heritage_judicial_effectiveness_physician_density_current_gap

**Verdict:** SUPPORTED — top-vs-bottom gap has expected sign + and Welch p=4.913e-10

## Design
- Heritage component: `judicial_effectiveness` using release year `2024`.
- Comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SH.MED.PHYS.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `3.41653488372093` over `43` countries.
- Low-market mean: `1.0942325581395351` over `43` countries.
- Difference, high minus low: `2.3223023255813953`.
- Welch p-value: `4.913173115714987e-10`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
