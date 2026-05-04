# Result card — heritage_tax_burden_account_ownership_current_gap

**Verdict:** REFUTED — top-vs-bottom gap has opposite sign and Welch p=2.887e-05

## Design
- Heritage component: `tax_burden` using release year `2024`.
- Comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:FX.OWN.TOTL.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `64.03464913514611` over `35` countries.
- Low-market mean: `85.00210690848276` over `35` countries.
- Difference, high minus low: `-20.967457773336648`.
- Welch p-value: `2.8873647212531564e-05`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
