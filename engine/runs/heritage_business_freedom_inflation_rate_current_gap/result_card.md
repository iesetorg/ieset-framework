# Result card — heritage_business_freedom_inflation_rate_current_gap

**Verdict:** SUPPORTED — top-vs-bottom gap has expected sign - and Welch p=0.001128

## Design
- Heritage component: `business_freedom` using release year `2024`.
- Comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:FP.CPI.TOTL.ZG` latest available country observation since `2018`.

## Estimate
- High-market mean: `2.347877948739941` over `42` countries.
- Low-market mean: `16.731493839801875` over `42` countries.
- Difference, high minus low: `-14.383615891061934`.
- Welch p-value: `0.0011282964179589762`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
