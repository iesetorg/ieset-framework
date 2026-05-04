# Result card — heritage_labor_freedom_trade_openness_current_gap

**Verdict:** SUPPORTED — top-vs-bottom gap has expected sign + and Welch p=0.001687

## Design
- Heritage component: `labor_freedom` using release year `2024`.
- Comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:NE.TRD.GNFS.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `111.83630621369316` over `39` countries.
- Low-market mean: `72.26192681608197` over `39` countries.
- Difference, high minus low: `39.574379397611196`.
- Welch p-value: `0.0016874415250390925`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
