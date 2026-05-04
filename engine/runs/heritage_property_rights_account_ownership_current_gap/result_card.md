# Result card — heritage_property_rights_account_ownership_current_gap

**Verdict:** SUPPORTED — top-vs-bottom gap has expected sign + and Welch p=6.11e-15

## Design
- Heritage component: `property_rights` using release year `2024`.
- Comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:FX.OWN.TOTL.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `95.32622158598745` over `36` countries.
- Low-market mean: `50.41101803195806` over `36` countries.
- Difference, high minus low: `44.9152035540294`.
- Welch p-value: `6.109727460647843e-15`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
