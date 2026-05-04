# Result card — heritage_trade_freedom_gdp_pc_ppp_current_gap

**Verdict:** SUPPORTED — top-vs-bottom gap has expected sign + and Welch p=2.533e-14

## Design
- Heritage component: `trade_freedom` using release year `2024`.
- Comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:NY.GDP.PCAP.PP.KD` latest available country observation since `2018`.

## Estimate
- High-market mean: `52195.573838500284` over `50` countries.
- Low-market mean: `9716.998926454688` over `43` countries.
- Difference, high minus low: `42478.574912045595`.
- Welch p-value: `2.5330048130642862e-14`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
