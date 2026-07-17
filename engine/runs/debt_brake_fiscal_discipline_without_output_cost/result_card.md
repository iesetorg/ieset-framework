# Schuldenbremse: debt discipline without output cost (2009-2019)

**Verdict:** SUPPORTED — Germany's debt-to-GDP rose by -6.5pp 2008-2019 vs donor-pool mean +23.4pp (-29.9pp differential, ≥10pp threshold met). Cumulative log-GDP-pc growth: Germany +12.6%, donor mean +8.2% (Germany 153% of donor mean, ≥90% threshold met). N=10 donor countries.

## Summary

- N = 10 of 10 donor countries with complete coverage.
- Δdebt-to-GDP 2008-2019: **Germany -6.5pp**, **donor-pool mean +23.4pp** (differential **-29.9pp**; threshold ≤ -10pp).
- Cumulative log-GDP-per-capita growth 2008-2019: **Germany +12.6%**, **donor mean +8.2%** (ratio **153%**; threshold ≥ 90%).
- Pre-trend (2000-2008): Germany +10.5% vs donor +11.5% (-0.9pp gap; within 5pp diagnostic band).
- Δfiscal balance (informative): Germany +1.6pp, donor mean +1.6pp.

## Method

Before/after panel comparison: Germany (treated) vs unweighted mean of
a 10-country donor pool of fiscal-rule-absent advanced 
Eurozone economies + UK. PRE=2008 (year before the constitutional 
amendment), POST=2019 (cleanest pre-COVID, pre-debt-brake-suspension 
year).

Outcomes:
1. Δdebt-to-GDP (IMF GGXWDG_NGDP, level)
2. Cumulative log-real-GDP-per-capita growth (WDI NY.GDP.PCAP.KD, log diff)
3. Pre-trend log-growth 2000-2008 (parallel-trend diagnostic)
4. Δgeneral-govt net lending / GDP (IMF GGXCNL_NGDP, informative)

**Spec downgrade.** Original spec called for synthetic-DID; the donor-
weight optimisation step is non-trivial and `synth_did` is not in the 
project venv. Per research documentation allowance, downgraded to a
transparent before/after comparison with an explicit pre-trend 
diagnostic. A real synth-DID would weight donors to match the pre-
period; this comparison instead reports the unweighted donor mean 
and the pre-period gap.

### Falsification thresholds

- PRIMARY 1 (debt): Germany Δdebt 2008-2019 must be ≥ 10pp lower than donor-pool mean.
- PRIMARY 2 (output): Germany cumulative log-growth 2008-2019 must be ≥ 90% of donor-pool mean.
- METHOD_VALID: at most 3 of 10 donors missing data.
- INFORMATIVE: pre-trend gap |2000-2008 Δlog-GDP-pc| ≤ 5pp for clean parallel-trend; if violated, verdict text flags caveat without 
overriding direction.

## Data

- imf:GGXWDG_NGDP (gross general-government debt / GDP)
- imf:GGXCNL_NGDP (general-government net lending / GDP)
- world_bank_wdi:NY.GDP.PCAP.KD (real GDP per capita, constant USD)

## Caveats

- Attribution to Schuldenbremse alone is contested. Confounds: ECB 
policy reaction post-2010, intra-Eurozone competitiveness gaps, 
German export demand boost from peripheral austerity, post-2010 
Hartz IV labour-market effects on unit labour costs.
- Donor pool is a fixed Eurozone+UK convenience sample. Including 
non-Eurozone non-fiscal-rule advanced economies (USA, JPN) would 
shift the donor mean substantially.
- 2008 pre-period endpoint is the eve of the Great Recession; both 
Germany and donors entered POST with elevated debt due to crisis 
interventions, which the simple endpoint comparison absorbs into 
Δdebt for both sides equally.
- The output ratio at low / negative donor means becomes unstable; 
code falls back to a 5pp absolute-gap test in that regime.
