# Result card — heritage_economic_freedom_gdp_pc_ppp_current_gap

**Verdict:** SUPPORTED — top-vs-bottom gap has expected sign + and Welch p=9.664e-14

## Design
- Heritage component: `overall_score` using release year `2024`.
- Comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:NY.GDP.PCAP.PP.KD` latest available country observation since `2018`.

## Estimate
- High-market mean: `55621.73322376715` over `43` countries.
- Low-market mean: `8966.498206066615` over `44` countries.
- Difference, high minus low: `46655.235017700536`.
- Welch p-value: `9.663728531741785e-14`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
