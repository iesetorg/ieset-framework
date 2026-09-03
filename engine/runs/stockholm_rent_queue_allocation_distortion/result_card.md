# Result card — stockholm_rent_queue_allocation_distortion

**Verdict:** INCONCLUSIVE_DATA_PENDING

**Reason:** 0 MET, 1 NOT_MET, 2 PENDING of 3; support threshold 2 not reachable on evaluated evidence

Pre-registered rule: SUPPORT if >= 2 of 3 metrics met; REFUTED if >= 1 confirmed NOT_MET with no path to support; otherwise INCONCLUSIVE_DATA_PENDING.

**Counts:** 0 MET · 1 NOT_MET · 1 PENDING_DATA · 1 PENDING_EVAL

**Primary country:** SWE

## Metric-by-metric

| # | Metric | Status | Observed | Threshold | Notes |
|---|---|:---:|---:|---|---|
| 1 | queue_dispersion_growth | NOT_MET | 0.00 [band_count_cv_change] | `cohort/district queue-time dispersion grows significantly over the sample` | queue-time band-count CV 0.00 (2017) -> 0.00 (2026); band-count dispersion is a coarse proxy for cohort/district queue dispersion (queue register carries band counts, not individual waits) |
| 2 | completions_offset_leg | PENDING_EVAL | 75.00 [completions_latest] | `municipal completions do not offset queue growth` | completions series on disk is municipality-aggregate; the queue-growth vs completions ratio needs the queue stock series (band counts are per-period counts, not the registered-stock total) — deferring to avoid a manufactured ratio |
| 3 | mobility_vs_comparison_municipalities | PENDING_DATA | — | `Stockholm tenant mobility at least 15% below comparison municipalities` | SCB panel on disk carries completions, dwelling stock, and rent per sqm; the tenant mobility measure is not landed |

## Claim

> Stockholm's rent-controlled allocation queue (Bostadsförmedlingen) creates measurable allocation distortion rather than clearing by preference: median queue time rises across cohorts and districts, insider tenants stay longer and move less than tenants in comparison Swedish municipalities, and the insider discount shows up as a widening gap between queue-wait valuation and realized rents, while municipal completions do not offset queue growth.

## Interpretation

Metrics evaluated against the pre-registered thresholds on the named derived panels; PENDING_* metrics disclose exactly which source is missing and are not counted toward support. This card is produced by scripts/run_derived_panel_checklist.py from the pinned panel vintages recorded per metric.

## Provenance

- spec: hypotheses/housing/stockholm_rent_queue_allocation_distortion.yaml
- runner: scripts/run_derived_panel_checklist.py
- run_utc: 2026-09-03T20:16:46.604459Z
- queue_dispersion_growth: data/derived/stockholm_bostadsformedlingen_queue_panel.parquet sha256=0b6f2f4e101837bb…
- completions_offset_leg: data/derived/sweden_scb_municipal_housing_panel.parquet sha256=588a192fb94bb745…
