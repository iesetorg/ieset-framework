# Result card — heritage_government_integrity_under5_mortality_current_gap

**Verdict:** SUPPORTED — top-vs-bottom gap has expected sign - and Welch p=1.139e-11

## Design
- Heritage component: `government_integrity` using release year `2024`.
- Comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SH.DYN.MORT` latest available country observation since `2018`.

## Estimate
- High-market mean: `6.755555555555555` over `45` countries.
- Low-market mean: `43.61555555555556` over `45` countries.
- Difference, high minus low: `-36.86000000000001`.
- Welch p-value: `1.1387895012006771e-11`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
