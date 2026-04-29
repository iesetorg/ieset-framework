# Milei reforms reduce Argentine inflation

**Verdict:** SUPPORTED — All three pre-registered tests hold. Median m/m inflation Oct'24-Feb'25 = 2.43% (<= 5.0%); Apr-Aug'25 = 1.88% (<= 3.0%); first sub-5% m/m print at t+5 (<= t+10). Pre-Milei median m/m 8.04% → t=0 print 25.47% → stabilisation as predicted.

## Summary

- Event date: 2023-12 (Milei inauguration); t=0 m/m print = 25.47% (post 54% peso devaluation).
- Pre-Milei median m/m inflation (t-11 through t=0): **8.04%/month**.
- **Primary 1** — window [t+10, t+14] (Oct 2024 - Feb 2025) median m/m: **2.43%** (threshold ≤ 5.0%). PASS.
- **Primary 2** — window [t+16, t+20] (Apr 2025 - Aug 2025) median m/m: **1.88%** (threshold ≤ 3.0%). PASS.
- **Primary 3** — months from inauguration to first m/m < 5%: **t+5** (threshold ≤ t+10). PASS.
- Method validity (INDEC monthly coverage Dec 2022 → Jun 2025 without gaps): OK.

## Method

Event-study presentation around the December 2023 Milei inauguration. INDEC IPC Nacional monthly index level (Dec 2016 = 100, series 148.3_INIVELNAL_DICI_M_26) is transformed to month-on-month percent change. The three pre-registered tests in the spec's `falsification.threshold` block are evaluated literally: window-A median ≤ 5%, window-B median ≤ 3%, and months-to-first-sub-5%-print ≤ 10. Verdict aggregates the three: 3/3 = SUPPORTED, 0/3 = refuted, 1-2/3 = partial. Method-valid gate requires gap-free INDEC coverage from t-12 through t+18.

Synthetic-control LatAm peer comparison and local-projection robustness (mentioned in `estimator.notes`) are deferred to v2; the three-threshold dispositive test is binding for v1 per the explicit pre-registration in `falsification.threshold`.

## Data

- indec:148.3_INIVELNAL_DICI_M_26 (monthly IPC Nacional index level, Dec 2016 = 100; coverage 2016-12-01 → 2026-03-01).
