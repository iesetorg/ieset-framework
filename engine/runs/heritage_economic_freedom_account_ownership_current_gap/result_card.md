# Result card — heritage_economic_freedom_account_ownership_current_gap

**Verdict:** SUPPORTED — top-vs-bottom gap has expected sign + and Welch p=1.188e-12

## Design
- Heritage component: `overall_score` using release year `2024`.
- Comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:FX.OWN.TOTL.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `92.13417080418789` over `34` countries.
- Low-market mean: `54.81109582627732` over `34` countries.
- Difference, high minus low: `37.32307497791057`.
- Welch p-value: `1.1875460138268908e-12`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
