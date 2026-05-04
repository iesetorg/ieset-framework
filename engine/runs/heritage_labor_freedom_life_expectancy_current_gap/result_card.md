# Result card — heritage_labor_freedom_life_expectancy_current_gap

**Verdict:** SUPPORTED — top-vs-bottom gap has expected sign + and Welch p=5.405e-08

## Design
- Heritage component: `labor_freedom` using release year `2024`.
- Comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SP.DYN.LE00.IN` latest available country observation since `2018`.

## Estimate
- High-market mean: `77.14158590785908` over `45` countries.
- Low-market mean: `69.68187416851441` over `44` countries.
- Difference, high minus low: `7.4597117393446695`.
- Welch p-value: `5.4052990878983504e-08`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
