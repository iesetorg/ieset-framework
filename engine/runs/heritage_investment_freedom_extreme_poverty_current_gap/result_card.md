# Result card — heritage_investment_freedom_extreme_poverty_current_gap

**Verdict:** SUPPORTED — top-vs-bottom gap has expected sign - and Welch p=0.0001674

## Design
- Heritage component: `investment_freedom` using release year `2024`.
- Comparison: top `25%` vs bottom `25%` of market-score countries.
- Outcome source: `world_bank_wdi:SI.POV.DDAY` latest available country observation since `2018`.

## Estimate
- High-market mean: `1.5499999999999998` over `32` countries.
- Low-market mean: `18.230952380952385` over `42` countries.
- Difference, high minus low: `-16.680952380952384`.
- Welch p-value: `0.00016735332815871886`.

## Caveat
This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.
