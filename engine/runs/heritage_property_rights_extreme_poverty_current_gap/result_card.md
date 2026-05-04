# Result card — heritage_property_rights_extreme_poverty_current_gap

**Verdict:** SUPPORTED — top-vs-bottom gap has expected sign - and Welch p=1.359e-05

## Design
- Heritage component: `property_rights` using release year `2024`.
- Comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SI.POV.DDAY` latest available country observation since `2018`.

## Estimate
- High-market mean: `0.41515151515151516` over `33` countries.
- Low-market mean: `24.763636363636365` over `33` countries.
- Difference, high minus low: `-24.34848484848485`.
- Welch p-value: `1.3590777913082726e-05`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
