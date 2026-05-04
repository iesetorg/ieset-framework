# Result card — heritage_business_freedom_gdp_pc_ppp_current_gap

**Verdict:** SUPPORTED — top-vs-bottom gap has expected sign + and Welch p=1.35e-17

## Design
- Heritage component: `business_freedom` using release year `2024`.
- Comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:NY.GDP.PCAP.PP.KD` latest available country observation since `2018`.

## Estimate
- High-market mean: `57806.00594839696` over `43` countries.
- Low-market mean: `5727.923406610958` over `43` countries.
- Difference, high minus low: `52078.082541786`.
- Welch p-value: `1.3498844205092798e-17`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
