# Result card — heritage_government_integrity_private_credit_depth_current_gap

**Verdict:** SUPPORTED — top-vs-bottom gap has expected sign + and Welch p=9.785e-10

## Design
- Heritage component: `government_integrity` using release year `2024`.
- Comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:FS.AST.PRVT.GD.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `83.691321111596` over `39` countries.
- Low-market mean: `24.273728531887546` over `39` countries.
- Difference, high minus low: `59.417592579708455`.
- Welch p-value: `9.785088661047226e-10`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
