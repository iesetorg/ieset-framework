# Result card — heritage_government_integrity_inflation_rate_current_gap

**Verdict:** SUPPORTED — top-vs-bottom gap has expected sign - and Welch p=0.006293

## Design
- Heritage component: `government_integrity` using release year `2024`.
- Comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:FP.CPI.TOTL.ZG` latest available country observation since `2018`.

## Estimate
- High-market mean: `2.3265288007329947` over `43` countries.
- Low-market mean: `14.11518162550692` over `43` countries.
- Difference, high minus low: `-11.788652824773926`.
- Welch p-value: `0.006292894002012242`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
