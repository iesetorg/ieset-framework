# Forward-guidance term-structure event study (post-2008 FOMC)

**Verdict:** SUPPORTED (US-FOMC daily channel only) — mean |ΔDGS2| on 5 FG days = 6.6 bp; placebo mean |Δ| = 1.3 bp (ratio 4.95x); DGS5 ratio = 4.06x. Mean |ΔDGS2| clears the 5bp magnitude bar AND the 2x placebo bar; DGS5 also clears the 1.5x informative bar. ECB/BoE/BoJ legs and intraday discrimination of sticky-info vs RE-signal remain METHOD_VALID data gaps.

## Summary

- Hand-coded FOMC forward-guidance event dates (n=5): 2008-12-16, 2011-08-09, 2012-09-13, 2013-12-18, 2015-09-17.
- Mean absolute 1-day Δ DGS2 on FG days: **6.6 bp** (n=5).
- Mean absolute 1-day Δ DGS2 on calendar-matched non-FOMC Wednesdays: **1.3 bp** (n=21).
- FG/placebo ratio (DGS2): **4.95x** (threshold 2.0x).
- DGS5 mean |Δ|: FG 11.2 bp vs placebo 2.8 bp (ratio 4.06x; informative threshold 1.5x).
- DGS10 mean |Δ|: FG 10.2 bp.

## Per-event 1-day yield changes (pp)

| Event | DGS2 Δ | DGS5 Δ | DGS10 Δ |
|---|---|---|---|
| 2008-12-16 | -0.100 | -0.160 | -0.160 |
| 2011-08-09 | -0.080 | -0.200 | -0.200 |
| 2012-09-13 | -0.010 | -0.050 | -0.020 |
| 2013-12-18 | -0.020 | +0.030 | +0.040 |
| 2015-09-17 | -0.120 | -0.120 | -0.090 |

## Method

Daily-frequency US-FOMC forward-guidance event study. For each of the 5 hand-coded FG announcement dates, compute the 1-day change in DGS2/DGS5/DGS10 (post-event-day close minus prior-trading-day close, in percentage points). Compare the mean absolute FG-day change against a calendar-matched placebo of all non-FOMC Wednesdays in the same months. The dispositive primary is mean |ΔDGS2|.

## METHOD_VALID data gaps

- **Intraday data**: the original spec asked for 30-minute windows.   Only daily FRED is on disk. Daily windows are noisier and cannot   attribute movement specifically to the FG headline.
- **Non-US central banks**: ECB / BoE / BoJ yield series and FG   event lists are not in the current vintage tree.
- **Pure-signal RE benchmark**: a calibrated NK model is required to   discriminate sticky-information from rational-expectations channels   per the original spec; no such model in repo. The daily test only   detects whether the term structure moved materially on FG days.

## Data

- fred:DGS2 — primary outcome (US 2y treasury yield, daily)
- fred:DGS5 — informative outcome (US 5y, daily)
- fred:DGS10 — informative outcome (US 10y, daily)
- fred:VIXCLS — backdrop control (CBOE VIX, daily)
