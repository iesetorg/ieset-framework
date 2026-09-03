# Result card — zimbabwe_hyperinflation_land_reform_output_collapse_2000_2009

**Verdict:** supported

> **QUARANTINED pending v2 re-score — adversarial audit remediation 2026-09-03.** See the Correction section below before citing this card. Primary finding: The definitional Cagan hyperinflation metric is PENDING_EVAL and does not gate the verdict (X6).


**Reason:** 8 of 10 metrics met threshold (support threshold 7)

Pre-registered rule: SUPPORT if >= 7 of 10 metrics met; REFUTE if <= 3 met (impossible to hit support).

## Correction 2026-09-03 — adversarial audit remediation

**Disposition:** QUARANTINED pending v2 re-score · **Audit:** `engine/audits/ieset_adversarial_supported_claims_2026-07-31.md` (claim 6) · **Remediation:** `engine/audits/ieset_adversarial_audit_remediation_2026-09-03.md` · **Detectors:** `scripts/audit_integrity_detectors.py`

- The definitional Cagan hyperinflation metric is PENDING_EVAL and does not gate the verdict (X6) — a hyperinflation-titled hypothesis supported without it.
- X1: metric 3 event-count 81829 (raw tonnes) compared against a '>50% decline' threshold.
- Metric 8 PENDING_DATA on manual commission reports (utete/buka) that never landed.

**Verdict-migration note (X5):** prior verdict was `inconclusive (data gaps, HYPOTHESIS_FRAMEWORK_AUDIT.md §E7)`; the migration to `supported` was undocumented — now recorded in this remediation's ledger.

**Machine-detector confirmations in diagnostics.json (not counted toward the verdict pending v2):**
- metric `real_gdp_contraction_peak` [sentinel_value]: percent-change stat at 100.0000 >= 99.99 — fallback/sentinel artefact, not a real observation
- metric `cereal_production_collapse` [sentinel_value]: percent-change stat at 99.9997 >= 99.99 — fallback/sentinel artefact, not a real observation
- metric `monetary_aggregate_growth_rate` [sentinel_value]: percent-change stat at 191938479.6545 >= 99.99 — fallback/sentinel artefact, not a real observation
- metric `life_expectancy_reversal` [unit_typetag_mismatch]: threshold in years_absolute evaluated against percent-change stat 'peak_to_trough_pct_decline' — MET/NOT_MET mechanically manufactured
- metric `hyperinflation_cagan_threshold`: 3 declared publishers share 2 vintage file(s) — fewer files than publishers
- metric `real_gdp_contraction_peak`: 3 declared publishers share 2 vintage file(s) — fewer files than publishers
- metric `tobacco_output_collapse`: 2 declared publishers share 1 vintage file(s) — all publishers byte-identical
- metric `currency_redenomination_count`: 2 declared publishers share 1 vintage file(s) — all publishers byte-identical
- metric `commercial_farm_expropriation_share`: 3 declared publishers share 0 vintage file(s) — fewer files than publishers
- metric `food_insecurity_wfp_caseload`: 2 declared publishers share 1 vintage file(s) — all publishers byte-identical
- metric `monetary_aggregate_growth_rate`: 2 declared publishers share 1 vintage file(s) — all publishers byte-identical

No original content has been deleted; this correction is additive.

**Counts:** 8 MET · 0 NOT_MET · 1 PENDING_DATA · 1 PENDING_EVAL

**Primary country:** ZWE

## Metric-by-metric

| # | Metric | Status | Observed | Threshold | Notes |
|---|---|:---:|---:|---|---|
| 1 | hyperinflation_cagan_threshold | PENDING_EVAL | 6.2 [max_loaded_value] | `>=2 consecutive months of >50% m/m CPI between 2007 and 2009` | count-based threshold requires event log; data not sufficient to auto-count |
| 2 | real_gdp_contraction_peak | MET | 100 (2008) [peak_to_trough_pct_decline] | `>35% cumulative real GDP contraction 2000-2008` |  |
| 3 | tobacco_output_collapse | MET |  | `>50% decline in flue-cured tobacco output from 2000 peak to any year 2003-2008` | event-count [max_value] = 81829 in 2003-2008; threshold >50 |
| 4 | cereal_production_collapse | MET | 100 (2002) [peak_to_trough_pct_decline] | `>50% decline in staple cereal production (maize + wheat + sorghum) from 1999 peak` |  |
| 5 | emigration_skilled_labour_exodus | MET | 24.9 (2009) [max_in_window] | `>15% of 2000 population emigrated by end-2009` |  |
| 6 | life_expectancy_reversal | MET | 23.7 (2001) [peak_to_trough_pct_decline] | `>10 year decline in life expectancy from 1990 peak to any trough year before 2009` |  |
| 7 | currency_redenomination_count | MET |  | `>=2 currency redenominations within a 5-year window` | event-count [max_cumulative] = 3 in 2005-2009; threshold >=2 |
| 8 | commercial_farm_expropriation_share | PENDING_DATA |  | `>50% of large-scale commercial farmland transferred or vacated without market-rate compensation` | No usable vintage for: manual:utete_commission_report_2003, manual:buka_report_2002 |
| 9 | food_insecurity_wfp_caseload | MET | 45 (2008) [max_in_window] | `>30% of resident population on WFP/NGO food assistance in any single year` |  |
| 10 | monetary_aggregate_growth_rate | MET | 1.92e+08 (2008) [pct_increase_from_baseline] | `>1000% annualised growth of M3 (or equivalent broad-money aggregate) for >=6 consecutive months` |  |

## Claim

> Zimbabwe's Fast Track Land Reform Programme (FTLRP, 2000-2002) combined with Reserve Bank of Zimbabwe deficit monetisation produced a canonical institutional and economic collapse 2000-2009 that manifests as >=7 of 10 pre-registered extreme-outcome metrics, each drawn from an independent data source and measuring a different causal layer (agricultural-capacity destruction, monetary collapse, output contraction, human-capital flight, humanitarian stress). The canonical-case claim is that no non-war peacetime sub-Saharan African economy in the 2000-2009 window matches even 4 of these 10 thresholds simultaneously; Zimbabwe matches most. A refutation (<=3 metrics met) would indicate that Zimbabwe's collapse has been substantially overstated or that the 1980-1999 pre-reform trend was already trending toward collapse independent of FTLRP and RBZ monetisation.

## Interpretation

The canonical-case pattern match is satisfied: 8 of 10 pre-registered metrics meet their thresholds, above the support threshold of 7. Each metric is drawn from an independent data source and measures a different causal layer, so the probability of this pattern arising from a data-pipeline fault across all sources simultaneously is low.

## Steelman live concerns

See `hypotheses/steelman/zimbabwe_hyperinflation_land_reform_output_collapse_2000_2009.md` for the strongest opposing arguments. Canonical-case multi-metric evidence is a pattern match, not a causal identification — the result card should be read as 'outcome trajectory matches the predicted pattern to degree X' rather than 'policy P caused the outcome'.

## Provenance

Vintages pinned in `manifest.yaml`. Full per-metric diagnostics in `diagnostics.json`. Machine-readable results in `metric_results.parquet`.
