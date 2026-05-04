# Result card — heritage_government_spending_private_consumption_pc_current_gap

**Verdict:** REFUTED — top-vs-bottom gap has opposite sign and Welch p=1.231e-09

## Design
- Heritage component: `government_spending` using release year `2024`.
- Comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:NE.CON.PRVT.PC.KD` latest available country observation since `2018`.

## Estimate
- High-market mean: `2615.553297351854` over `37` countries.
- Low-market mean: `15613.881415227888` over `37` countries.
- Difference, high minus low: `-12998.328117876034`.
- Welch p-value: `1.230796089503238e-09`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
