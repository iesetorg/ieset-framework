# Result card — heritage_tax_burden_private_consumption_pc_current_gap

**Verdict:** REFUTED — top-vs-bottom gap has opposite sign and Welch p=0.0001134

## Design
- Heritage component: `tax_burden` using release year `2024`.
- Comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:NE.CON.PRVT.PC.KD` latest available country observation since `2018`.

## Estimate
- High-market mean: `6446.522834410872` over `38` countries.
- Low-market mean: `15433.729304699911` over `38` countries.
- Difference, high minus low: `-8987.206470289038`.
- Welch p-value: `0.00011341673040011055`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
