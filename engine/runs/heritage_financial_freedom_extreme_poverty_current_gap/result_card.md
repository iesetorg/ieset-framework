# Result card — heritage_financial_freedom_extreme_poverty_current_gap

**Verdict:** SUPPORTED — top-vs-bottom gap has expected sign - and Welch p=1.133e-06

## Design
- Heritage component: `financial_freedom` using release year `2024`.
- Comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SI.POV.DDAY` latest available country observation since `2018`.

## Estimate
- High-market mean: `1.430612244897959` over `49` countries.
- Low-market mean: `20.627659574468087` over `47` countries.
- Difference, high minus low: `-19.19704732957013`.
- Welch p-value: `1.132929445531082e-06`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
