# Result card — heritage_economic_freedom_private_consumption_pc_current_gap

**Verdict:** SUPPORTED — top-vs-bottom gap has expected sign + and Welch p=8.971e-12

## Design
- Heritage component: `overall_score` using release year `2024`.
- Comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:NE.CON.PRVT.PC.KD` latest available country observation since `2018`.

## Estimate
- High-market mean: `19688.819607227975` over `37` countries.
- Low-market mean: `2169.066205341057` over `37` countries.
- Difference, high minus low: `17519.75340188692`.
- Welch p-value: `8.971317527374089e-12`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
