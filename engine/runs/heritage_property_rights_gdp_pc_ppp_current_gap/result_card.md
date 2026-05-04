# Result card — heritage_property_rights_gdp_pc_ppp_current_gap

**Verdict:** SUPPORTED — top-vs-bottom gap has expected sign + and Welch p=4.779e-15

## Design
- Heritage component: `property_rights` using release year `2024`.
- Comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:NY.GDP.PCAP.PP.KD` latest available country observation since `2018`.

## Estimate
- High-market mean: `54600.2781839895` over `44` countries.
- Low-market mean: `9047.997413664603` over `44` countries.
- Difference, high minus low: `45552.2807703249`.
- Welch p-value: `4.77949062181188e-15`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
