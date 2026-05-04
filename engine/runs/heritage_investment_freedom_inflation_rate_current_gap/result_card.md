# Result card — heritage_investment_freedom_inflation_rate_current_gap

**Verdict:** SUPPORTED — top-vs-bottom gap has expected sign - and Welch p=0.01501

## Design
- Heritage component: `investment_freedom` using release year `2024`.
- Comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:FP.CPI.TOTL.ZG` latest available country observation since `2018`.

## Estimate
- High-market mean: `4.00763716134024` over `59` countries.
- Low-market mean: `12.610537100010257` over `54` countries.
- Difference, high minus low: `-8.602899938670017`.
- Welch p-value: `0.015007559291585447`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
