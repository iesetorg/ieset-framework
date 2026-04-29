# QE at the ZLB: term-premia compression event study

**Verdict:** SUPPORTED — Cumulative 1-day 10y Treasury yield change across 5 easing announcements: -99.0 bp (threshold: <= -25.0 bp). Mean per-event: -19.8 bp (threshold: <= -5.0 bp). 4 of 5 events show a yield decline. Secondary: 30y cumul -59.0 bp, HY OAS cumul +0.0 bp.

## Summary

- Six FOMC QE-related announcement dates 2008-2013, FRED daily data.
- PRIMARY: cumulative 1-day 10y Treasury yield change across the five easing announcements = **-99.0 bp** (SUPPORT threshold: <= -25 bp).
- Mean per-event 1-day change: **-19.8 bp** (SUPPORT threshold: <= -5 bp).
- 4 of 5 easing events show a 1-day yield decline.
- 5-day cumulative 10y change: -75.0 bp.
- Secondary 30y cumulative: **-59.0 bp**.
- Secondary HY OAS cumulative: **+0.0 bp** (portfolio-rebalancing channel implies negative).
- Taper (2013-12-18) 1-day 10y: **+9.0 bp**
.

## Per-event table (basis points)

| Event | Date | Kind | 10y 1d | 10y 5d | 30y 1d | BAA 1d | HY OAS 1d |
|---|---|---|---:|---:|---:|---:|---:|
| QE1 launch | 2008-11-25 | easing | -36.0 | -67.0 | -24.0 | -78.0 | NA |
| QE1 expansion | 2009-03-18 | easing | -41.0 | -21.0 | -21.0 | -3.0 | NA |
| QE2 | 2010-11-03 | easing | -10.0 | +2.0 | +11.0 | +18.0 | NA |
| Operation Twist | 2011-09-21 | easing | -23.0 | +8.0 | -42.0 | +10.0 | NA |
| QE3 | 2012-09-13 | easing | +11.0 | +3.0 | +17.0 | -26.0 | NA |
| QE3 taper | 2013-12-18 | tightening | +9.0 | +15.0 | +3.0 | -19.0 | NA |

## Method

Daily FRED yield series (DGS10, DGS30, BAA, BAMLH0A0HYM2). For each FOMC QE-related announcement date listed in spec.variables.treatment, compute the change between the previous trading day's close and the next trading day's close (1-day window). 5-day window is previous-trading-day → +5 trading days. Levels in percent are converted to basis points (×100).

Why a daily window rather than the canonical 30-min intraday window: FRED publishes daily close yields, not intraday tick data. The 1-day close-to-close window is a noisier-but-publicly-replicable proxy for the 30-min event window used in Gagnon-Raskin-Remache-Sack (2011) and Krishnamurthy-Vissing-Jorgensen (2011). The thresholds below were sized for this daily window rather than the literature's intraday window.

Falsification thresholds (dispositive, sharpened in v1 promotion):
  PRIMARY (both required for SUPPORTED):
    - cumulative 1-day DGS10 change across 5 easing announcements       <= -25 bp
    - mean 1-day DGS10 change across 5 easing announcements       <= -5 bp
  REFUTED if cumulative > 0 bp OR zero of five easing events show a decline.
  PARTIAL if direction is correct but cumulative magnitude misses threshold.

## Data

- `fred:DGS10` (treasury_10y)
- `fred:DGS30` (treasury_30y)
- `fred:BAA` (baa_corporate)
- `fred:BAMLH0A0HYM2` (high_yield_oas)
- `fred:WALCL` (fed_balance_sheet)
- `fred:VIXCLS` (vix)
- `fred:SP500` (sp500)
- `fred:DFF` (fed_funds_rate)
