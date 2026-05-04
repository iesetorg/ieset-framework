# Result card — heritage_labor_freedom_under5_mortality_current_gap

**Verdict:** SUPPORTED — top-vs-bottom gap has expected sign - and Welch p=4.063e-06

## Design
- Heritage component: `labor_freedom` using release year `2024`.
- Comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SH.DYN.MORT` latest available country observation since `2018`.

## Estimate
- High-market mean: `12.13111111111111` over `45` countries.
- Low-market mean: `35.150000000000006` over `44` countries.
- Difference, high minus low: `-23.018888888888895`.
- Welch p-value: `4.063152924801819e-06`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
