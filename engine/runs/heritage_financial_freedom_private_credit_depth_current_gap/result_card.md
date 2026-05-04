# Result card — heritage_financial_freedom_private_credit_depth_current_gap

**Verdict:** SUPPORTED — top-vs-bottom gap has expected sign + and Welch p=7.411e-09

## Design
- Heritage component: `financial_freedom` using release year `2024`.
- Comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:FS.AST.PRVT.GD.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `76.26690314196016` over `60` countries.
- Low-market mean: `33.34281069918175` over `56` countries.
- Difference, high minus low: `42.92409244277841`.
- Welch p-value: `7.410707749647597e-09`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
