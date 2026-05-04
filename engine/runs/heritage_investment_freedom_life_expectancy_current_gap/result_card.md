# Result card — heritage_investment_freedom_life_expectancy_current_gap

**Verdict:** SUPPORTED — top-vs-bottom gap has expected sign + and Welch p=5.19e-13

## Design
- Heritage component: `investment_freedom` using release year `2024`.
- Comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SP.DYN.LE00.IN` latest available country observation since `2018`.

## Estimate
- High-market mean: `78.96954715447153` over `60` countries.
- Low-market mean: `69.89697398373983` over `45` countries.
- Difference, high minus low: `9.072573170731701`.
- Welch p-value: `5.190402446123448e-13`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
