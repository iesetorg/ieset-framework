# Result card — heritage_economic_freedom_life_expectancy_current_gap

**Verdict:** SUPPORTED — top-vs-bottom gap has expected sign + and Welch p=1.772e-15

## Design
- Heritage component: `overall_score` using release year `2024`.
- Comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SP.DYN.LE00.IN` latest available country observation since `2018`.

## Estimate
- High-market mean: `79.96730654101997` over `44` countries.
- Low-market mean: `68.66273503325942` over `44` countries.
- Difference, high minus low: `11.304571507760542`.
- Welch p-value: `1.7720719008121838e-15`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
