# Result card — heritage_tax_burden_employment_rate_current_gap

**Verdict:** PARTIAL — gap sign/magnitude not decisive (diff=0.5323, p=0.8257)

## Design
- Heritage component: `tax_burden` using release year `2024`.
- Comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SL.EMP.TOTL.SP.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `58.48637209302326` over `43` countries.
- Low-market mean: `57.954069767441865` over `43` countries.
- Difference, high minus low: `0.5323023255813979`.
- Welch p-value: `0.8256636442370264`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
