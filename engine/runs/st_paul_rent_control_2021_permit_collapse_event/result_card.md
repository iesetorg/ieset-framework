# Result card — st_paul_rent_control_2021_permit_collapse_event

**Verdict:** REFUTED

**Reason:** the Minneapolis control shows a comparable permit decline over the same window (spec rejection branch: macro shock, not the ordinance)

Pre-registered rule: SUPPORT if >= 3 of 4 metrics met; REFUTED if >= 1 confirmed NOT_MET with no path to support; otherwise INCONCLUSIVE_DATA_PENDING.

**Counts:** 1 MET · 1 NOT_MET · 1 PENDING_DATA · 1 PENDING_EVAL

**Primary country:** USA

## Metric-by-metric

| # | Metric | Status | Observed | Threshold | Notes |
|---|---|:---:|---:|---|---|
| 1 | stpaul_permit_gap | MET | -670.27 [permit_mean_change_units] | `post-ordinance permit decline in St Paul vs pre-window` | mean annual units 1796 (2017-2021) vs 1125 (2022-2024) (units column: total_units) |
| 2 | minneapolis_control_leg | NOT_MET | -1555.00 [permit_mean_change_units] | `Minneapolis does not show a comparable permit decline (macro-shock control)` | Minneapolis mean annual units 3443 -> 1888 |
| 3 | amendment_reversal_leg | PENDING_EVAL | 813.33 [permit_mean_units] | `post-2022-09 new-construction permits recover >= 30% of the decline within 12 months` | annual Census BPS aggregation cannot isolate post-September-2022 filings within 2022; monthly filing data (not landed) required for the reversal leg |
| 4 | eviction_filings_leg | PENDING_DATA | — | `eviction filings around the ordinance` | Eviction Lab tracking system not landed (city ingestion queue item) |

## Claim

> St Paul Minnesota's November 2021 rent-stabilization ordinance (3 percent annual cap, no new-construction exemption at passage) caused a decline in building-permit activity beyond what rate-cycle and macro conditions explain: post-ordinance permits in St Paul fall at least 50 percent below the synthetic-control gap within 24 months, the decline concentrates in previously-exempt new construction, and the September 2022 amendment (new-construction exemption) partially reverses it, while Minneapolis shows no comparable decline over the same window.

## Interpretation

Metrics evaluated against the pre-registered thresholds on the named derived panels; PENDING_* metrics disclose exactly which source is missing and are not counted toward support. This card is produced by scripts/run_derived_panel_checklist.py from the pinned panel vintages recorded per metric.

## Provenance

- spec: hypotheses/housing/st_paul_rent_control_2021_permit_collapse_event.yaml
- runner: scripts/run_derived_panel_checklist.py
- run_utc: 2026-09-03T20:16:44.918024Z
- stpaul_permit_gap: data/derived/us_city_permits_panel.parquet sha256=f7167140cce20413…
- minneapolis_control_leg: data/derived/us_city_permits_panel.parquet sha256=f7167140cce20413…
- amendment_reversal_leg: data/derived/us_city_permits_panel.parquet sha256=f7167140cce20413…
