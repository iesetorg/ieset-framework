# Result card — catalonia_reference_rent_contract_supply_response_2020

**Verdict:** INCONCLUSIVE_DATA_PENDING

**Reason:** 0 MET, 1 NOT_MET, 1 PENDING of 2; support threshold 1 not reachable on evaluated evidence

Pre-registered rule: SUPPORT if >= 1 of 2 metrics met; REFUTED if >= 1 confirmed NOT_MET with no path to support; otherwise INCONCLUSIVE_DATA_PENDING.

**Counts:** 0 MET · 1 NOT_MET · 1 PENDING_DATA · 0 PENDING_EVAL

**Primary country:** ESP

## Metric-by-metric

| # | Metric | Status | Observed | Threshold | Notes |
|---|---|:---:|---:|---|---|
| 1 | catalonia_contract_volume_trend | NOT_MET | 146220.67 [annual_contract_mean_change] | `new-contract volume falls after the September 2020 reference-price law (Catalonia-wide trend)` | mean annual contracts 369871 (2018-2020) vs 516092 (2021-2022); Catalonia-wide — the designation-boundary contrast is blocked (see next metric) |
| 2 | stressed_area_boundary_contrast | PENDING_DATA | — | `treated (stressed-area) municipalities show significant new-contract and listing declines vs non-designated` | the stressed-area designation list (which municipalities, which dates) is not landed; without it the treated/control DiD cannot be evaluated — this metric is the spec's decisive rejection leg |

## Claim

> Catalonia's 2020 reference-price law (September 2020, applying rent caps to municipalities designated as stressed housing-market areas) reduced new rental-contract volume and listings in designated municipalities relative to non-designated Catalan and bordering autonomous-community municipalities within 18 months of designation, with a measurable shift of formal contracts toward exempt or shorter-duration categories and no offsetting rise in non-designated neighbor rents.

## Interpretation

Metrics evaluated against the pre-registered thresholds on the named derived panels; PENDING_* metrics disclose exactly which source is missing and are not counted toward support. This card is produced by scripts/run_derived_panel_checklist.py from the pinned panel vintages recorded per metric.

## Provenance

- spec: hypotheses/housing/catalonia_reference_rent_contract_supply_response_2020.yaml
- runner: scripts/run_derived_panel_checklist.py
- run_utc: 2026-09-03T20:16:46.104672Z
- catalonia_contract_volume_trend: data/derived/catalonia_rent_contracts_panel.parquet sha256=49850c145e5921a2…
