# Result card — heritage_government_spending_trade_openness_current_gap

**Verdict:** REFUTED — top-vs-bottom gap has opposite sign and Welch p=0.0008018

## Design
- Heritage component: `government_spending` using release year `2024`.
- Comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:NE.TRD.GNFS.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `66.25219145160206` over `39` countries.
- Low-market mean: `112.46033484621374` over `39` countries.
- Difference, high minus low: `-46.20814339461168`.
- Welch p-value: `0.000801833921471484`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
