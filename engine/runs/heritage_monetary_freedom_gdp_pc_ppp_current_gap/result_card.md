# Result card — heritage_monetary_freedom_gdp_pc_ppp_current_gap

**Verdict:** SUPPORTED — top-vs-bottom gap has expected sign + and Welch p=0.0003883

## Design
- Heritage component: `monetary_freedom` using release year `2024`.
- Comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:NY.GDP.PCAP.PP.KD` latest available country observation since `2018`.

## Estimate
- High-market mean: `34172.77852638495` over `43` countries.
- Low-market mean: `15393.561498991674` over `43` countries.
- Difference, high minus low: `18779.21702739328`.
- Welch p-value: `0.0003883246400411493`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
