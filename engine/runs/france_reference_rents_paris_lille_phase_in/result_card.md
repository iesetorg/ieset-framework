# Result card — france_reference_rents_paris_lille_phase_in

**Verdict:** INCONCLUSIVE_DATA_PENDING

**Reason:** 0 MET, 0 NOT_MET, 2 PENDING of 2; support threshold 1 not reachable on evaluated evidence

Pre-registered rule: SUPPORT if >= 1 of 2 metrics met; REFUTED if >= 1 confirmed NOT_MET with no path to support; otherwise INCONCLUSIVE_DATA_PENDING.

**Counts:** 0 MET · 0 NOT_MET · 2 PENDING_DATA · 0 PENDING_EVAL

**Primary country:** FRA

## Metric-by-metric

| # | Metric | Status | Observed | Threshold | Notes |
|---|---|:---:|---:|---|---|
| 1 | paris_rent_vs_ceiling_gap | PENDING_DATA | — | `observed new-lease rents sit materially below ceilings in binding years` | reference-rents panel carries reference/ceiling/floor levels but no observed new-lease rent column; the OLL observations dataset is not landed |
| 2 | off_on_off_phase_in_contrast | PENDING_DATA | — | `annulment-window coefficient indistinguishable from zero; Lille onset; Lyon control` | reference-rents panel on disk covers PARIS 2019-2025 only; the 2015-2017 and 2017-2019 annulment windows, Lille (2020), and the Lyon/Villeurbanne control are required for the spec's off-on-off design and are not landed |

## Claim

> The French encadrement des loyers rent-reference systems bind on new-lease rents in the treated cities: Paris (2015-2017, annulled, reinstated 2019) and Lille (2020) show lower new-lease rent growth relative to the Lyon/Villeurbanne control window and untreated inner suburbs during active years, with the effect absent during the 2017-2019 Paris annulment window, and a composition shift toward exempt categories during binding years.

## Interpretation

Metrics evaluated against the pre-registered thresholds on the named derived panels; PENDING_* metrics disclose exactly which source is missing and are not counted toward support. This card is produced by scripts/run_derived_panel_checklist.py from the pinned panel vintages recorded per metric.

## Provenance

- spec: hypotheses/housing/france_reference_rents_paris_lille_phase_in.yaml
- runner: scripts/run_derived_panel_checklist.py
- run_utc: 2026-09-03T20:16:47.124818Z
