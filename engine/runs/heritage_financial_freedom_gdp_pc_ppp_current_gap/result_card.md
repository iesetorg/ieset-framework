# Result card — heritage_financial_freedom_gdp_pc_ppp_current_gap

**Verdict:** SUPPORTED — top-vs-bottom gap has expected sign + and Welch p=5.646e-14

## Design
- Heritage component: `financial_freedom` using release year `2024`.
- Comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:NY.GDP.PCAP.PP.KD` latest available country observation since `2018`.

## Estimate
- High-market mean: `45686.86049564366` over `64` countries.
- Low-market mean: `10937.198003295043` over `68` countries.
- Difference, high minus low: `34749.662492348616`.
- Welch p-value: `5.646487087986855e-14`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
