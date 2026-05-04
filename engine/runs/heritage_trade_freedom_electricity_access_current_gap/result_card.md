# Result card — heritage_trade_freedom_electricity_access_current_gap

**Verdict:** SUPPORTED — top-vs-bottom gap has expected sign + and Welch p=7.134e-08

## Design
- Heritage component: `trade_freedom` using release year `2024`.
- Comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:EG.ELC.ACCS.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `99.82600000000001` over `50` countries.
- Low-market mean: `71.91136363636363` over `44` countries.
- Difference, high minus low: `27.914636363636376`.
- Welch p-value: `7.134257320092994e-08`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
