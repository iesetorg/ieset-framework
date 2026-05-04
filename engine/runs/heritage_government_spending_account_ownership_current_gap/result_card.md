# Result card — heritage_government_spending_account_ownership_current_gap

**Verdict:** REFUTED — top-vs-bottom gap has opposite sign and Welch p=8.136e-13

## Design
- Heritage component: `government_spending` using release year `2024`.
- Comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:FX.OWN.TOTL.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `53.45774581812141` over `34` countries.
- Low-market mean: `93.02735652325623` over `34` countries.
- Difference, high minus low: `-39.56961070513482`.
- Welch p-value: `8.136109943277555e-13`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
