# Result card — heritage_judicial_effectiveness_employment_rate_current_gap

**Verdict:** SUPPORTED — top-vs-bottom gap has expected sign + and Welch p=0.08895

## Design
- Heritage component: `judicial_effectiveness` using release year `2024`.
- Comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SL.EMP.TOTL.SP.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `58.30993181818182` over `44` countries.
- Low-market mean: `54.33138636363637` over `44` countries.
- Difference, high minus low: `3.978545454545454`.
- Welch p-value: `0.08894850086988391`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
