# Result card — heritage_government_spending_inflation_rate_current_gap

**Verdict:** REFUTED — top-vs-bottom gap has opposite sign and Welch p=0.009956

## Design
- Heritage component: `government_spending` using release year `2024`.
- Comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:FP.CPI.TOTL.ZG` latest available country observation since `2018`.

## Estimate
- High-market mean: `14.273211759796178` over `42` countries.
- Low-market mean: `3.08226655900758` over `42` countries.
- Difference, high minus low: `11.190945200788597`.
- Welch p-value: `0.009955570531153599`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
