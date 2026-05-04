# Result card — heritage_trade_freedom_private_credit_depth_current_gap

**Verdict:** SUPPORTED — top-vs-bottom gap has expected sign + and Welch p=1.257e-09

## Design
- Heritage component: `trade_freedom` using release year `2024`.
- Comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:FS.AST.PRVT.GD.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `72.52989911336888` over `45` countries.
- Low-market mean: `28.872922530955776` over `38` countries.
- Difference, high minus low: `43.65697658241311`.
- Welch p-value: `1.2571701206916986e-09`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
