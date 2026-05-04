# Result card — heritage_financial_freedom_employment_rate_current_gap

**Verdict:** SUPPORTED — top-vs-bottom gap has expected sign + and Welch p=0.06798

## Design
- Heritage component: `financial_freedom` using release year `2024`.
- Comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SL.EMP.TOTL.SP.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `59.069421874999996` over `64` countries.
- Low-market mean: `55.48923880597015` over `67` countries.
- Difference, high minus low: `3.580183069029843`.
- Welch p-value: `0.06797606866768509`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
