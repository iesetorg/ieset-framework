# Result card — heritage_government_integrity_life_expectancy_current_gap

**Verdict:** SUPPORTED — top-vs-bottom gap has expected sign + and Welch p=3.397e-19

## Design
- Heritage component: `government_integrity` using release year `2024`.
- Comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SP.DYN.LE00.IN` latest available country observation since `2018`.

## Estimate
- High-market mean: `80.12920813008131` over `45` countries.
- Low-market mean: `68.0498108401084` over `45` countries.
- Difference, high minus low: `12.079397289972903`.
- Welch p-value: `3.397098726748392e-19`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
