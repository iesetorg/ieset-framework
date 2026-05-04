# Result card — heritage_trade_freedom_private_consumption_pc_current_gap

**Verdict:** SUPPORTED — top-vs-bottom gap has expected sign + and Welch p=7.077e-13

## Design
- Heritage component: `trade_freedom` using release year `2024`.
- Comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:NE.CON.PRVT.PC.KD` latest available country observation since `2018`.

## Estimate
- High-market mean: `16384.572469316045` over `49` countries.
- Low-market mean: `2219.9361439491904` over `38` countries.
- Difference, high minus low: `14164.636325366853`.
- Welch p-value: `7.076927496890106e-13`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
