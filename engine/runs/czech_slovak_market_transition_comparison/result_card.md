# Result card — czech_slovak_market_transition_comparison

**Verdict:** INCONCLUSIVE_DATA_PENDING — registered 1993-to-2024 long-difference cannot be estimated: Fraser market-institutions endpoints and 2024 government-consumption endpoints are absent

## Frozen two-spec preflight

The frozen two-spec design requires a panel decomposition and a 1993-to-2024 long-difference across market_institutions_index, fdi_inflows_pct_gdp, govt_consumption_pct_gdp. None of the 11 declared countries have all three channels at both endpoints.
The Fraser market-institutions series has no 1993 or 2024 endpoint for Czechia and Slovakia; the WDI government-consumption series lacks 2024 values. Substituting nearby years would change the frozen test.
The old generic panel run also treated a 1993 baseline GDP control as a time-varying series from the same WDI GDP source in 11 countries. Its R²=1 near-zero estimate cannot grade the frozen design. That run is preserved under `historical/` and receives no evidence credit.

All frozen coefficient and long-difference decisions remain unassessable until the declared endpoints exist or a new prospective design is registered.

Spec SHA-256: `461590f032201d9a0f20d32012ad32e874ba8830331ef75bc25c1a00a2fa2784`
Input-panel SHA-256: `9a8be008dc93dbb8d7dadd12df7257e0ba2fee757e52ee2311c3bb7c9abba925`
