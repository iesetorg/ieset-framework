# Post-2008 OECD growth-emissions path

**Verdict:** SUPPORTED — Mean OECD log-growth post-2008 (excl. 2020): +1.65%/yr (≤ 2.0% threshold). Mean per-capita emissions in 2023 are at 68% of 2008 baseline; the 1.5C-consistent benchmark for 2023 is 66% — emissions are +2pp above the path. 11 of 26 OECD countries are above their 1.5C share.

## Summary

- Mean OECD annual log-growth 2009-2023 (excluding COVID 2020): **+1.65%/yr** (median: +1.89%/yr).
- Threshold for the degrowth claim's 'slowed-growth' premise: ≤ 2.0%/yr. Premise holds.
- Mean OECD 2023 per-capita CO2 emissions: **68% of 2008 baseline**.
- 1.5C-consistent benchmark fraction at 2023: **66%** (linear path 1.0 → 0.50 by 2030).
- 11 of 26 OECD countries with data are above their 1.5C share.

## Method

Two simple primary tests against the spec's stated falsification rule:

1. Mean log-difference of NY.GDP.MKTP.KD across the 26 OECD-country panel, year-on-year 2009-2023, dropping any pair touching 2020.
2. 2023 ÷ 2008 ratio of per-capita CO2 emissions, country-mean.

The 1.5C-consistent benchmark used here (linear path to -50% by 2030) is a permissive reading of fast-mitigation IPCC SSP1-1.9 scenarios — slower-mitigation scenarios require steeper cuts and would push the benchmark fraction lower, making the hypothesis harder to refute. Robustness to alternative benchmarks is left as a v2 question.

## Data

- world_bank_wdi:NY.GDP.MKTP.KD
- owid:co2-emissions-per-capita
