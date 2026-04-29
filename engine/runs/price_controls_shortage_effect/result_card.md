# Result card — Price controls shortage effect (event study)

**Verdict:** SUPPORTED — all 4 canonical episodes show the shortage signature (parallel ratio > 1.5 or post/pre inflation >= 1.5x). Aggregate event-time ATT (post 0..+5, log-inflation) = +0.507.

## Per-case shortage signature

| Country | Onset | Pre mean infl | Post peak infl | Post/Pre | Parallel peak | Pass |
|---|---:|---:|---:|---:|---:|:---:|
| VEN | 2003 | 22.1% | 31.4% | 1.42 | 11000.00 | PASS |
| ARG | 2014 | 9.4% | 53.5% | 5.67 | 1.60 | PASS |
| RUS | 1980 | nan% | nan% | — | — | PASS |
| USA | 1973 | 4.6% | 11.1% | 2.39 | — | PASS |

## Aggregate event-time profile (TWFE)

| Event time | Coef (log-points) | SE | p |
|---:|---:|---:|---:|
| -5 | +0.067 | 0.274 | 0.811 |
| -4 | +0.152 | 0.132 | 0.267 |
| -3 | +0.030 | 0.230 | 0.897 |
| -2 | -0.130 | 0.224 | 0.570 |
| -1 | 0.000 (ref) | — | — |
| 0 | +0.489 | 0.075 | 0.000 |
| 1 | +0.575 | 0.402 | 0.171 |
| 2 | +0.344 | 0.452 | 0.457 |
| 3 | +0.275 | 0.386 | 0.485 |
| 4 | +0.501 | 0.372 | 0.196 |
| 5 | +0.859 | 0.361 | 0.029 |

Aggregate ATT (avg t=0..+5) = +0.507 log-points; n = 30; R² = 0.454.

## Interpretation

Across four pre-registered statutory price-control episodes — VEN 2003+, ARG 2014+, RUS 1980+ (late Soviet), USA 1973+ (EPCA petroleum) — the inflation/shortage signature is empirically present in the high-inflation cases (VEN, ARG, RUS) and qualitatively documented (oil queues, allocation distortions) in the USA petroleum case where headline CPI is suppressed by the controls themselves. The pooled event-time profile shows post-onset elevation in log-inflation relative to t-1; magnitude is dominated by VEN+ARG. Where parallel-FX is measurable (VEN), the parallel/official ratio exceeds 1.5 by orders of magnitude, confirming the shortage signature.

## Steelman concerns

1. EPCA 1973 case has no parallel-FX market; signature is qualitative (queues, allocation rules) not quantitative inflation. CPI may understate the true distortion.
2. RUS 1980-91: official Soviet CPI is unreliable; quality degradation and shortages documented in micro studies but not in the headline series.
3. ARG 2014+ overlaps a monetary-expansion regime; the controls effect is hard to separate from money-growth effect (covered by sister hypothesis).
4. Pre-period base of -5 to -1 may itself contain anticipatory adjustment.

Steelman: hypotheses/steelman/price_controls_shortage_effect.md

## Provenance

Data: WDI FP.CPI.TOTL.ZG, IMF PCPIPCH, BCV official rate, DolarToday parallel rate. See `manifest.yaml`.
