# Result card — heritage_business_freedom_under5_mortality_current_gap

**Verdict:** SUPPORTED — top-vs-bottom gap has expected sign - and Welch p=4.45e-16

## Design
- Heritage component: `business_freedom` using release year `2024`.
- Comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SH.DYN.MORT` latest available country observation since `2018`.

## Estimate
- High-market mean: `5.613636363636364` over `44` countries.
- Low-market mean: `54.72727272727272` over `44` countries.
- Difference, high minus low: `-49.11363636363635`.
- Welch p-value: `4.450017963419529e-16`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
