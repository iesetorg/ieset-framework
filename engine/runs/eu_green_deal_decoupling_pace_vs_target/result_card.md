# EU Green Deal: pace of decoupling vs 1.5C-consistent target

**Verdict:** SUPPORTED — EU panel shows partial decoupling 2019->2023: mean per-capita CO2 -18.3%, mean per-capita real GDP +4.6%. 13/16 countries showed both falling emissions and rising GDP. Pace is BELOW 1.5C path: 2023 mean emissions at 83% of 2019 vs benchmark 82% (gap +2pp). 11/16 above the 1.5C share.

## Summary

- 16-country EU panel, baseline 2019 (pre-Green-Deal), assessment 2023.
- Mean per-capita CO2 change 2019->2023: **-18.3%** (threshold for decoupling premise: ≤ -2%).
- Mean per-capita real GDP change 2019->2023: **+4.6%** (threshold ≥ +1%).
- 13/16 countries showed both emissions falling AND GDP rising.
- 2023 mean per-capita CO2 = **83% of 2019**.
- 1.5C-consistent linear benchmark for 2023 = **82%** (path 2019->-50% by 2030).
- 11/16 countries are above (slower than) their 1.5C share.

## Method

Two dispositive primary tests:

1. Relative decoupling: mean log-change of OWID per-capita CO2 from 2019 to 2023 (≤ -2%) AND mean log-change of WDI per-capita real GDP (≥ +1%) over the same window.
2. Pace gap: mean ratio of 2023 per-capita CO2 to 2019 per-capita CO2, compared against a linear 1.5C-consistent benchmark (path 2019 = 1.0 to 2030 = 0.50, so benchmark at 2023 ≈ 0.818).

Real GDP per capita is constructed as NY.GDP.MKTP.KD / SP.POP.TOTL to keep the comparison on a per-capita basis (CO2 series is already per-capita).

**Caveat (from spec.disclosure):** territorial CO2 (OWID convention) ignores carbon content of imports; consumption-based EU emissions may show a smaller decline. The linear 1.5C benchmark is a permissive reading of fast-mitigation IPCC SSP1-1.9 — slower scenarios require steeper near-term cuts and would push the benchmark fraction lower (making the 'pace insufficient' leg easier to satisfy).

## Data

- world_bank_wdi:NY.GDP.MKTP.KD
- world_bank_wdi:SP.POP.TOTL
- owid:co2-emissions-per-capita
