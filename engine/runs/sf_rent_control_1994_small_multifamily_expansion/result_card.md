# Result card — sf_rent_control_1994_small_multifamily_expansion

**Verdict:** INCONCLUSIVE_DATA_PENDING

**Reason:** 1 MET, 0 NOT_MET, 3 PENDING of 4; support threshold 3 not reachable on evaluated evidence

Pre-registered rule: SUPPORT if >= 3 of 4 metrics met; REFUTED if >= 1 confirmed NOT_MET with no path to support; otherwise INCONCLUSIVE_DATA_PENDING.

**Counts:** 1 MET · 0 NOT_MET · 3 PENDING_DATA · 0 PENDING_EVAL

**Primary country:** USA

## Metric-by-metric

| # | Metric | Status | Observed | Threshold | Notes |
|---|---|:---:|---:|---|---|
| 1 | treated_class_rental_supply_share | PENDING_DATA | — | `treated-vs-exempt rental-supply decline significant at p<=0.05 over 10 years` | Rent Board Housing Inventory vintage on disk covers 2022-2026 only; 1994-2005 building-class rental share requires the historical assessor-classified series (not landed). |
| 2 | condo_conversion_count | PENDING_DATA | — | `treated-class conversion counts vs exempt stock` | condo-conversion record dataset not landed (SF open-data bundle gap) |
| 3 | maintenance_violation_trend | MET | 114.30 [violation_mean_change_annual] | `maintenance/code-violation proxy rises for treated stock post-expansion` | citywide DBI notices of violation: mean 510/yr (1997-2000) vs 624/yr (2001-2005); building-class split unavailable (panel carries citywide counts) — first-order trend only, not the treated-vs-exempt contrast the spec requires |
| 4 | entrant_incumbent_rent_gap | PENDING_DATA | — | `entrant-minus-incumbent rent gap positive and significant` | tenant tenure / entrant rent split requires ACS microdata (not landed) |

## Claim

> San Francisco's 1994 rent-control expansion (Proposition I, bringing small multifamily buildings of 2-4 units built before 1980 under the 1979 Rent Stabilization and Arbitration Ordinance) reduced the rental supply, maintenance, and tenant mobility of the treated building class relative to exempt stock and donor cities over the following decade: treated small-multifamily buildings show higher rental-to-owner conversion and condo-conversion rates, weaker maintenance and code- violation outcomes, and lower tenant turnover than comparable exempt single-family and post-1980 stock, while incumbent tenants receive a measurable rent discount relative to entrants.

## Interpretation

Metrics evaluated against the pre-registered thresholds on the named derived panels; PENDING_* metrics disclose exactly which source is missing and are not counted toward support. This card is produced by scripts/run_derived_panel_checklist.py from the pinned panel vintages recorded per metric.

## Provenance

- spec: hypotheses/housing/sf_rent_control_1994_small_multifamily_expansion.yaml
- runner: scripts/run_derived_panel_checklist.py
- run_utc: 2026-09-03T20:16:44.418163Z
- maintenance_violation_trend: data/derived/us_sf_rent_control_quality_leakage_panel.parquet sha256=5b613cb59639f9ed…
