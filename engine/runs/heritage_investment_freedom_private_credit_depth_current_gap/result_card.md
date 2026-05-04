# Result card — heritage_investment_freedom_private_credit_depth_current_gap

**Verdict:** SUPPORTED — top-vs-bottom gap has expected sign + and Welch p=0.0003064

## Design
- Heritage component: `investment_freedom` using release year `2024`.
- Comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:FS.AST.PRVT.GD.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `69.28649043271797` over `55` countries.
- Low-market mean: `39.94596725708862` over `47` countries.
- Difference, high minus low: `29.34052317562935`.
- Welch p-value: `0.000306351382685692`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
