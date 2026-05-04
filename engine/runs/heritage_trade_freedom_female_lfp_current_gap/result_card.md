# Result card — heritage_trade_freedom_female_lfp_current_gap

**Verdict:** SUPPORTED — top-vs-bottom gap has expected sign + and Welch p=0.09061

## Design
- Heritage component: `trade_freedom` using release year `2024`.
- Comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SL.TLF.CACT.FE.ZS` latest available country observation since `2018`.

## Estimate
- High-market mean: `56.49706382978722` over `47` countries.
- Low-market mean: `51.208860465116274` over `43` countries.
- Difference, high minus low: `5.288203364670949`.
- Welch p-value: `0.0906052301184799`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
