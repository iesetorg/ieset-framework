# Result card — heritage_government_integrity_account_ownership_current_gap

**Verdict:** SUPPORTED — top-vs-bottom gap has expected sign + and Welch p=2.705e-17

## Design
- Heritage component: `government_integrity` using release year `2024`.
- Comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:FX.OWN.TOTL.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `93.38422441321214` over `36` countries.
- Low-market mean: `46.486080396091495` over `36` countries.
- Difference, high minus low: `46.89814401712064`.
- Welch p-value: `2.7045175626897565e-17`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
