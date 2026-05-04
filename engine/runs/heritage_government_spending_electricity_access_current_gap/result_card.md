# Result card — heritage_government_spending_electricity_access_current_gap

**Verdict:** REFUTED — top-vs-bottom gap has opposite sign and Welch p=9.142e-08

## Design
- Heritage component: `government_spending` using release year `2024`.
- Comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:EG.ELC.ACCS.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `69.51363636363637` over `44` countries.
- Low-market mean: `96.79545454545455` over `44` countries.
- Difference, high minus low: `-27.28181818181818`.
- Welch p-value: `9.142314837265882e-08`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
