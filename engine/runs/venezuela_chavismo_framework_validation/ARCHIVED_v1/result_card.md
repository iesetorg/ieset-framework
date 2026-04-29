# Result card — Venezuela Chavismo framework validation

**Verdict:** weakened — phase signs not all negative; pre-trend lead |t|=4.03 ≥ 1.65

Pre-registered falsification: cumulative 2020 gap ≤ -0.30 log-points (~ -26%) AND all three phase coefficients additively negative AND pre-trend placebo |t| < 1.65.

## Nested DiD (log GDP per capita PPP, country + year FE)

| Phase | β | SE | 95% CI | p | t |
|---|---:|---:|:---:|---:|---:|
| post-1999 Chávez | +0.546 | 0.100 | [+0.349, +0.744] | 0.000 | +5.47 |
| post-2003 PDVSA + controls | -0.105 | 0.092 | [-0.286, +0.076] | 0.255 | -1.14 |
| post-2014 Maduro + oil crash | -1.190 | 0.072 | [-1.332, -1.049] | 0.000 | -16.65 |

Sum of three phase coefficients: -0.749 log-points (≈ -53% cumulative DiD-identified effect).

## Descriptive cumulative divergence

- 1996–1998 baseline VEN-vs-donor-avg gap: +0.005 log-points
- 2020 VEN-vs-donor-avg gap: -1.563 log-points
- Cumulative divergence 1996-1998 → 2020: **-1.568** log-points (≈ -79%)
- 2023 VEN-vs-donor-avg gap: -0.947 log-points

## Pre-trend check

Lead indicator 1996–1998 (pre-1999): |t| = 4.03 — FLAG: pre-trend detected

## Interpretation

The validation did not cleanly pass pre-registered thresholds. This is an informative refutation — either the data substrate has a gap, the donor pool is inadequate, or the hypothesis as specified is too specific. Possible remedies: (1) use a narrower donor pool matched on oil-share-of-GDP; (2) run synthetic control per-country-pair; (3) extend sample to include pre-1996 data where feasible.

## Steelman-live concerns (should shape reading)

1. Oil-price crash 2014–2016 is a large exogenous shock hitting Venezuela disproportionately; donor-pool oil exposure is imperfect control.
2. US sanctions post-2015 (and secondary sanctions post-2019) are a separate treatment the framework's coding does not isolate.
3. Distributional gains 2003–2012 (poverty, literacy, health) are not in this result card; complete analysis would include UNDP HDI + WHO GHO outcomes.

## Provenance

Reproduces from vintages in `manifest.yaml`. See `replication.py`.
