# Result card — heritage_financial_freedom_private_consumption_pc_current_gap

**Verdict:** SUPPORTED — top-vs-bottom gap has expected sign + and Welch p=4.367e-13

## Design
- Heritage component: `financial_freedom` using release year `2024`.
- Comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:NE.CON.PRVT.PC.KD` latest available country observation since `2018`.

## Estimate
- High-market mean: `15429.44789005316` over `60` countries.
- Low-market mean: `2376.7297932572633` over `55` countries.
- Difference, high minus low: `13052.718096795896`.
- Welch p-value: `4.366534901837061e-13`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
