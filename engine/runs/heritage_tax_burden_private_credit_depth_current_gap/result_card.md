# Result card — heritage_tax_burden_private_credit_depth_current_gap

**Verdict:** REFUTED — top-vs-bottom gap has opposite sign and Welch p=0.003502

## Design
- Heritage component: `tax_burden` using release year `2024`.
- Comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:FS.AST.PRVT.GD.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `49.48217477090786` over `38` countries.
- Low-market mean: `78.34684141948178` over `38` countries.
- Difference, high minus low: `-28.864666648573916`.
- Welch p-value: `0.0035017094389201177`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
