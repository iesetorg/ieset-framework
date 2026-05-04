# Result card — heritage_investment_freedom_electricity_access_current_gap

**Verdict:** SUPPORTED — top-vs-bottom gap has expected sign + and Welch p=8.423e-06

## Design
- Heritage component: `investment_freedom` using release year `2024`.
- Comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:EG.ELC.ACCS.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `99.15333333333335` over `60` countries.
- Low-market mean: `79.82444444444444` over `45` countries.
- Difference, high minus low: `19.328888888888912`.
- Welch p-value: `8.423482576839433e-06`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
