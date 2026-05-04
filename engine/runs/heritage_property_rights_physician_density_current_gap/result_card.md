# Result card — heritage_property_rights_physician_density_current_gap

**Verdict:** SUPPORTED — top-vs-bottom gap has expected sign + and Welch p=8.624e-10

## Design
- Heritage component: `property_rights` using release year `2024`.
- Comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SH.MED.PHYS.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `3.7048604651162798` over `43` countries.
- Low-market mean: `1.3054883720930233` over `43` countries.
- Difference, high minus low: `2.3993720930232563`.
- Welch p-value: `8.623514300292223e-10`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
