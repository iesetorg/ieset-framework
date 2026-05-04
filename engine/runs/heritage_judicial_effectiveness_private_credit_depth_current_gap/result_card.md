# Result card — heritage_judicial_effectiveness_private_credit_depth_current_gap

**Verdict:** SUPPORTED — top-vs-bottom gap has expected sign + and Welch p=3.006e-09

## Design
- Heritage component: `judicial_effectiveness` using release year `2024`.
- Comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:FS.AST.PRVT.GD.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `82.54774582470993` over `39` countries.
- Low-market mean: `26.5066089014496` over `39` countries.
- Difference, high minus low: `56.04113692326034`.
- Welch p-value: `3.005836110975566e-09`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
