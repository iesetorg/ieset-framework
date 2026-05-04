# Result card — heritage_judicial_effectiveness_under5_mortality_current_gap

**Verdict:** SUPPORTED — top-vs-bottom gap has expected sign - and Welch p=4.272e-10

## Design
- Heritage component: `judicial_effectiveness` using release year `2024`.
- Comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SH.DYN.MORT` latest available country observation since `2018`.

## Estimate
- High-market mean: `6.930434782608694` over `46` countries.
- Low-market mean: `37.97555555555556` over `45` countries.
- Difference, high minus low: `-31.045120772946866`.
- Welch p-value: `4.2724393132015177e-10`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
