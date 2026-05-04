# Result card — heritage_government_spending_private_credit_depth_current_gap

**Verdict:** REFUTED — top-vs-bottom gap has opposite sign and Welch p=7.064e-07

## Design
- Heritage component: `government_spending` using release year `2024`.
- Comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:FS.AST.PRVT.GD.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `28.478283059303347` over `38` countries.
- Low-market mean: `71.69332211284251` over `38` countries.
- Difference, high minus low: `-43.21503905353916`.
- Welch p-value: `7.06392841609379e-07`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
