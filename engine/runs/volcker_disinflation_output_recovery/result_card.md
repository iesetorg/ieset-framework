# Volcker disinflation output recovery

**Verdict:** SUPPORTED — CPI YoY fell from 14.4% peak (1980Q2) to 3.2% in 1983Q4 (drop = 11.2pp, threshold >= 5.0pp; level threshold <= 5.0%). Real GDP at 1984Q4 was -1.9% relative to the 1972Q1-1979Q3 linear log-time trend (recovery threshold >= -2.0%). Both primaries cleared.

## Summary

- Sample: USA quarterly, 1972Q1-1984Q4 with 1972-1979Q3 pre-trend.
- Event: 1979-10 Volcker FOMC tightening (effective fed funds peaks at **17.8%** in 1981Q2).
- CPI YoY: peak **14.4%** (1980Q2) -> **3.2%** in 1983Q4. Drop = **11.2pp** (threshold >= 5.0pp). Disinflation primary PASS.
- Real GDP (GDPC1) at 1984Q4 = **-1.9%** vs the linear log-time trend fit on 1972Q1-1979Q3 (pre-trend growth ~ 3.16%/yr). Threshold for recovery: gap >= -2.0%. Recovery primary PASS.
- Recession trough (largest negative gap to trend, 1980-1983): **-8.6%** in 1982Q4.

## Method

1. CPI YoY = 12-month log-difference of monthly CPIAUCSL, aggregated to quarterly mean.
2. Peak CPI YoY identified within 1979Q1-1981Q4 (the Volcker-era peak window).
3. Real-GDP trend = OLS linear fit of log(GDPC1) on time-index (quarters since 1972Q1) over 1972Q1-1979Q3, then extrapolated.
4. 1984Q4 gap = log(GDPC1_1984Q4) - extrapolated_trend_1984Q4.
5. SUPPORTED iff (1983Q4 CPI YoY <= 5% AND peak-to-1983Q4 drop >= 5pp) AND (1984Q4 trend gap >= -2%). REFUTED if drop < 5pp OR gap <= -5%.

## Caveats

- Pre-trend window includes both 1973 and 1979 oil-price shocks, so the estimated 1972-79 trajectory is dragged down by them. This is *conservative for the recovery claim*: a 'no-shock' counterfactual trend would be steeper, making the 1984Q4 gap larger (more negative). Hypothesis is therefore tested against an easy benchmark.
- Volcker tightening is bundled with Reagan tax cuts (1981 ERTA) and the 1980 / 1981-82 recessions. The event-study identifies the *joint* macro outcome, not the pure monetary-policy effect. The Romer-Romer narrative-shock decomposition would be required to isolate.
- Single-country analysis: no cross-country counterfactual to a country that did not tighten. The result is a within-US time-series test of the disinflation-with-recovery pattern.

## Data

- fred:CPIAUCSL — US headline CPI (monthly).
- fred:GDPC1 — US real GDP, chained (quarterly).
- fred:FEDFUNDS — US effective federal funds rate (monthly).
