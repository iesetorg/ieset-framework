# US post-2008 GDP-per-capita vs real-median-income divergence

**Verdict:** refuted — Both primary tests failed. Cumulative log gap = +0.039 (below 0.15 threshold) AND median income grew +15.9 log-pp (not flat-or-declining). GDP/cap +19.9 log-pp; the divergence and stagnation premises both miss.

## Summary

- US real GDP per capita 2008 = $53,443 → 2023 = $65,187 (cumulative log change **+19.9 log-pp**).
- US real median household income 2008 = $70,520 → 2023 = $82,690 (cumulative log change **+15.9 log-pp**).
- Cumulative log gap (GDP/cap minus median income) = **+3.9 log-pp**. Threshold for SUPPORTED: gap >= 15 log-pp AND median income <= 0.
- PRIMARY 1 (gap >= 0.15): FAIL.
- PRIMARY 2 (median income flat-or-declining): FAIL.

## Method

Endpoint comparison of two indexed series for the United States, 2008 → 2023:

1. **Real GDP per capita** — World Bank WDI `NY.GDP.PCAP.KD` (constant-USD GDP per capita).
2. **Real median household income** — FRED `MEHOINUSA672N` (annual real median household income in 2023 CPI-U-RS dollars).

Cumulative log change is `ln(value_2023 / value_2008)` for each series. The PRIMARY statistic is the difference of the two log changes (the divergence gap). The hypothesis is SUPPORTED only if BOTH the gap is >= 0.15 log-points (~+16pp) AND median income is flat-or-declining (cumulative log change <= 0).

## Steelman if the verdict is missing

Median household income is a **weaker** proxy than the ISEW/GPI the original claim references. A true GPI run would deduct ecological costs (depletion, climate damage), defensive expenditures, and an inequality adjustment that median income ignores; on the degrowth school's reading those deductions widen the divergence. The cleanest steelman: even if median income rose, the GPI version of welfare may still have stagnated. ISEW/GPI series are not on disk in any publisher vintage, so this hypothesis cannot dispositively REFUTE the broader GPI framing — only the GDP-vs-median-income framing. A v2 promotion that wires in a Kubiszewski/Talberth GPI vintage would tighten the test.

## Data

- world_bank_wdi:NY.GDP.PCAP.KD
- fred:MEHOINUSA672N
