# Movement-vintage hypothesis integrity review — 2026-10-10

This review covers the four saved hypothesis specifications that reference the May 16 movement-derived vintages. It distinguishes the national-scope repair in `scripts/build_movement_vintages.py` from defects already present in saved run evidence. The May 16 movement files, manifests, result cards, diagnostics, and pre-registered specifications are preserved.

| Hypothesis | Prior public tier | Movement vintage in measured fit? | Decision |
| --- | --- | --- | --- |
| `catch_up_capital_deepening_not_tfp` | archive | No. Its bespoke replication uses PWT and fixed episode starts. | Remain archive; no movement-scope rescore. |
| `developmentalist_growth_premium_low_income_only` | calibration | Yes, developmentalism alignment. | Quarantine public and school credit because the saved packet and run provenance conflict. |
| `market_reform_duration_growth_persistence` | calibration | No. The generic multi-country runner measured the first, Fraser EFW treatment; its movement treatment was not used in the coefficient. | No movement-scope rescore. Its design completeness remains a separate review. |
| `resource_developmentalism_rent_seeking_trap` | featured | Yes, resource-developmentalism scalar. | Quarantine featured and school credit because the scalar does not identify the registered subtype contrast or product-level diversification outcome. |

## National-scope effect

The movement corpus includes California and EU-wide records that must not be assigned to national country-year rows. The corrected vintage builder filters them and starts the default grid at the earliest national movement year, 1789. The six excluded subnational/supranational records have no developmentalism alignment, and neither of the two measured developmentalism treatments derives a positive contribution from them. This correction alone does not justify changing any saved coefficient or verdict. Historical May 16 movement files remain pinned for those runs; any new national-only vintage must use a new timestamp and a new source manifest.

## Developmentalist growth provenance hold

The `engine/runs/developmentalist_growth_premium_low_income_only/manifest.yaml` and `evidence_packet.yaml` describe a May 15 preflight with two missing series, no input vintages, and a reported coefficient of −0.459. The current `diagnostics.json` and `result_card.md` describe a May 16 fit with coefficient +0.1632, p=0.688, 583 observations in 23 countries. The packet's hash list no longer identifies the current diagnostics and card. Its source list cannot establish which exact movement and PWT bytes produced the May 16 coefficient. The generic panel fit is also a single treatment coefficient, while the registered rule requires income-stage contrasts. There is no defensible deterministic packet-only repair, so the historical files remain untouched and the public result is held through `engine/public_evidence_quarantines.json`. Return requires exact historical input custody and a reconciled packet, or a new prospective source-pinned run of the staged design.

## Resource-developmentalism measurement hold

The saved May 18 run manifest pins `resource_developmentalism@2026-05-16T084233Z.parquet` (SHA256 `1c0c493af87d02d54e6ae8fd90c4cd51f986007747b78dfd18780d6eacc5786c`) and reports a broad-proxy coefficient −0.008094, p=0.758, 1,320 observations in 73 countries. The run's own caveat says this is a proxy screen. The May 17 subtype audit finds 540 generic-positive country-years in its reviewed countries, but 326 are mixed/excluded/shock rather than clean treatment. On the clean sidecar panel, the registered country-and-year fixed-effects model cannot estimate a treatment effect because eligible treatment has no within-country variation. The official product-level export-concentration payload is also absent. The historical PARTIAL result remains inspectable; the external quarantine removes featured and school credit pending an estimable, source-pinned subtype design and outcome.

## Release boundary

This correction changes public evidence classification only. It makes no claim that either historical result is false, that national-scope filtering changes its reported coefficient, or that a future rerun will support the claim. Recompute the evidence tier ledger, public census, and conversion funnel from the registry and verify the public copies before using revised counts.
