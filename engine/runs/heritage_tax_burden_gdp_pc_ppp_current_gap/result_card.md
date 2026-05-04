# Result card — heritage_tax_burden_gdp_pc_ppp_current_gap

**Verdict:** PARTIAL — gap sign/magnitude not decisive (diff=-9554, p=0.1259)

## Design
- Heritage component: `tax_burden` using release year `2024`.
- Comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:NY.GDP.PCAP.PP.KD` latest available country observation since `2018`.

## Estimate
- High-market mean: `28079.47393818604` over `43` countries.
- Low-market mean: `37633.26400263118` over `44` countries.
- Difference, high minus low: `-9553.790064445137`.
- Welch p-value: `0.12588550600927945`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
