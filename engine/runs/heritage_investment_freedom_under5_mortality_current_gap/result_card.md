# Result card — heritage_investment_freedom_under5_mortality_current_gap

**Verdict:** SUPPORTED — top-vs-bottom gap has expected sign - and Welch p=4.756e-08

## Design
- Heritage component: `investment_freedom` using release year `2024`.
- Comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SH.DYN.MORT` latest available country observation since `2018`.

## Estimate
- High-market mean: `9.015254237288135` over `59` countries.
- Low-market mean: `34.82666666666666` over `45` countries.
- Difference, high minus low: `-25.811412429378528`.
- Welch p-value: `4.755913919562112e-08`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
