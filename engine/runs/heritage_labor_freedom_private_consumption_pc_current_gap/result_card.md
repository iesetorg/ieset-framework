# Result card — heritage_labor_freedom_private_consumption_pc_current_gap

**Verdict:** SUPPORTED — top-vs-bottom gap has expected sign + and Welch p=2.846e-10

## Design
- Heritage component: `labor_freedom` using release year `2024`.
- Comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:NE.CON.PRVT.PC.KD` latest available country observation since `2018`.

## Estimate
- High-market mean: `16947.44396746856` over `38` countries.
- Low-market mean: `2634.53292086204` over `37` countries.
- Difference, high minus low: `14312.91104660652`.
- Welch p-value: `2.845549572070016e-10`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
