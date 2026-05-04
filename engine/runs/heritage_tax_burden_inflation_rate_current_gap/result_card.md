# Result card — heritage_tax_burden_inflation_rate_current_gap

**Verdict:** PARTIAL — gap sign/magnitude not decisive (diff=-2.41, p=0.6539)

## Design
- Heritage component: `tax_burden` using release year `2024`.
- Comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:FP.CPI.TOTL.ZG` latest available country observation since `2018`.

## Estimate
- High-market mean: `5.851955046322062` over `42` countries.
- Low-market mean: `8.261928284874202` over `42` countries.
- Difference, high minus low: `-2.4099732385521397`.
- Welch p-value: `0.6538688483322518`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
