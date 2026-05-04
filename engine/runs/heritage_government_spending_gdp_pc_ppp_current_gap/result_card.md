# Result card — heritage_government_spending_gdp_pc_ppp_current_gap

**Verdict:** REFUTED — top-vs-bottom gap has opposite sign and Welch p=3.227e-09

## Design
- Heritage component: `government_spending` using release year `2024`.
- Comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:NY.GDP.PCAP.PP.KD` latest available country observation since `2018`.

## Estimate
- High-market mean: `11420.810206378666` over `43` countries.
- Low-market mean: `44314.325764691836` over `43` countries.
- Difference, high minus low: `-32893.51555831317`.
- Welch p-value: `3.2272557748465243e-09`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
