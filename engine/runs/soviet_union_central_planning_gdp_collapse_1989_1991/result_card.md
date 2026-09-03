# Result card — soviet_union_central_planning_gdp_collapse_1989_1991

**Verdict:** supported

> **QUARANTINED pending v2 re-score — adversarial audit remediation 2026-09-03.** See the Correction section below before citing this card. Primary finding: X2: `gdp_contraction_peak_to_trough` observed 99.99999929185707 (diagnostics.json:28).


**Reason:** 9 of 10 metrics met threshold (support threshold 7)

Pre-registered rule: SUPPORT if >= 7 of 10 metrics met; REFUTE if <= 3 met (impossible to hit support).

## Correction 2026-09-03 — adversarial audit remediation

**Disposition:** QUARANTINED pending v2 re-score · **Audit:** `engine/audits/ieset_adversarial_supported_claims_2026-07-31.md` (claim 4) · **Remediation:** `engine/audits/ieset_adversarial_audit_remediation_2026-09-03.md` · **Detectors:** `scripts/audit_integrity_detectors.py`

- X2: `gdp_contraction_peak_to_trough` observed 99.99999929185707 (diagnostics.json:28) — physically impossible value scored MET.
- X1 unit mismatches: life expectancy '>5 year decline' vs 11.56 percent; fertility '>0.5 TFR decline' vs 98.2 percent; poverty '>20 pp' vs 6.98 percent (spurious NOT_MET).
- X3: every metric has fewer distinct vintage files than declared publishers (e.g. da0c27… shared by rosstat:demographic_yearbook, human_mortality_database:RUS, who_gho) — the card's 'independent data sources' interpretation line is void.
- Window stretch: claim is 1989–1991 collapse; metrics run to 1996–1999 (the transition depression — a distinct causal event).

**Verdict-migration note (X5):** prior verdict was `inconclusive (data gaps, HYPOTHESIS_FRAMEWORK_AUDIT.md §E7)`; the migration to `supported` was undocumented — now recorded in this remediation's ledger.

**Machine-detector confirmations in diagnostics.json (not counted toward the verdict pending v2):**
- metric `gdp_contraction_peak_to_trough` [sentinel_value]: percent-change stat at 100.0000 >= 99.99 — fallback/sentinel artefact, not a real observation
- metric `life_expectancy_male_collapse` [unit_typetag_mismatch]: threshold in years_absolute evaluated against percent-change stat 'peak_to_trough_pct_decline' — MET/NOT_MET mechanically manufactured
- metric `gini_inequality_surge` [unit_typetag_mismatch]: threshold in gini_points evaluated against percent-change stat 'pct_increase_from_baseline' — MET/NOT_MET mechanically manufactured
- metric `fertility_collapse_tfr` [unit_typetag_mismatch]: threshold in years_absolute+tfr_points evaluated against percent-change stat 'peak_to_trough_pct_decline' — MET/NOT_MET mechanically manufactured
- metric `poverty_headcount_surge` [unit_typetag_mismatch]: threshold in percentage_points evaluated against percent-change stat 'pct_increase_from_baseline' — MET/NOT_MET mechanically manufactured
- metric `gdp_contraction_peak_to_trough`: 3 declared publishers share 2 vintage file(s) — fewer files than publishers
- metric `industrial_output_collapse`: 3 declared publishers share 1 vintage file(s) — all publishers byte-identical
- metric `life_expectancy_male_collapse`: 3 declared publishers share 1 vintage file(s) — all publishers byte-identical
- metric `hyperinflation_1992_1995`: 3 declared publishers share 2 vintage file(s) — fewer files than publishers
- metric `gini_inequality_surge`: 3 declared publishers share 1 vintage file(s) — all publishers byte-identical
- metric `fertility_collapse_tfr`: 3 declared publishers share 2 vintage file(s) — fewer files than publishers
- metric `poverty_headcount_surge`: 3 declared publishers share 1 vintage file(s) — all publishers byte-identical
- metric `emigration_fsu_diaspora`: 4 declared publishers share 2 vintage file(s) — fewer files than publishers
- metric `currency_regime_failure_ruble`: 3 declared publishers share 1 vintage file(s) — all publishers byte-identical
- metric `reform_depth_conditioned_recovery`: 3 declared publishers share 2 vintage file(s) — fewer files than publishers

No original content has been deleted; this correction is additive.

**Counts:** 9 MET · 1 NOT_MET · 0 PENDING_DATA · 0 PENDING_EVAL

**Primary country:** RUS

## Metric-by-metric

| # | Metric | Status | Observed | Threshold | Notes |
|---|---|:---:|---:|---|---|
| 1 | gdp_contraction_peak_to_trough | MET | 100 (1996) [peak_to_trough_pct_decline] | `>30% cumulative real GDP contraction 1989-1998` |  |
| 2 | industrial_output_collapse | MET | 56.4 (1998) [peak_to_trough_pct_decline] | `>40% decline in industrial production index 1990-1998` |  |
| 3 | life_expectancy_male_collapse | MET | 11.6 (1994) [peak_to_trough_pct_decline] | `>5 year decline in male life expectancy at birth between 1987 and any trough year before 2000` |  |
| 4 | hyperinflation_1992_1995 | MET |  | `>=2 consecutive calendar years of >500% annualised CPI inflation 1992-1995` | max consecutive years >500.0 = 2 in 1992-1995 |
| 5 | gini_inequality_surge | MET | 1.54 (1996) [pct_increase_from_baseline] | `>0.15 Gini increase between 1988 and 1998` |  |
| 6 | fertility_collapse_tfr | MET | 98.2 (1999) [peak_to_trough_pct_decline] | `>0.5 decline in TFR between 1987 and any trough year before 2001` |  |
| 7 | poverty_headcount_surge | NOT_MET | 6.98 (1998) [pct_increase_from_baseline] | `>20 percentage point increase in poverty headcount (moderate line) 1988-1998` |  |
| 8 | emigration_fsu_diaspora | MET | 1.95 (1996) [max_in_window_fallback] | `>1 million recorded emigrants from FSU territory to OECD destinations 1989-1996` |  |
| 9 | currency_regime_failure_ruble | MET |  | `>=2 major currency-regime events (confiscatory reform, redenomination, or sovereign default + devaluation >30%) within a 10-year window` | event-count [max_cumulative] = 3 in 1989-1998; threshold >=2 |
| 10 | reform_depth_conditioned_recovery | MET |  | `>20 percentage point gap in 2000-GDP-pc-relative-to-1989 between deep-reform (EST, LVA, POL, CZE) and shallow-reform (BLR, UKR, UZB, TKM) FSU/CEE republics` | two-list gap = 37.37 pp (deep-reform median 105.5 vs shallow-reform median 68.2; ref 2000/1989) |

## Claim

> The Soviet central-planning system, having already exhibited TFP stagnation 1970-1989, underwent a canonical institutional and economic collapse 1989-1998 as plan-enforcement was withdrawn without functioning market institutions in place. The collapse manifests as ≥7 of 10 pre-registered extreme- outcome metrics drawn from independent data sources and measuring distinct causal layers (real output, industrial production, hyperinflation, male mortality, demographic collapse, inequality surge, emigration, currency regime failure, poverty headcount, reform-depth-conditioned recovery). The canonical-case claim is that no non-war peacetime transition in the 1989-1998 global panel matches even 4 of these 10 thresholds simultaneously except the FSU bloc itself. A refutation (≤3 metrics met) would indicate that the post- Soviet collapse has been overstated by Western reconstructions, or that the political-shock explanation (Gorbachev / Yeltsin choices) dominates the institutional-exhaustion explanation in a way that rules out the canonical-case framing.

## Interpretation

The canonical-case pattern match is satisfied: 9 of 10 pre-registered metrics meet their thresholds, above the support threshold of 7. Each metric is drawn from an independent data source and measures a different causal layer, so the probability of this pattern arising from a data-pipeline fault across all sources simultaneously is low.

## Steelman live concerns

See `hypotheses/steelman/soviet_union_central_planning_gdp_collapse_1989_1991.md` for the strongest opposing arguments. Canonical-case multi-metric evidence is a pattern match, not a causal identification — the result card should be read as 'outcome trajectory matches the predicted pattern to degree X' rather than 'policy P caused the outcome'.

## Provenance

Vintages pinned in `manifest.yaml`. Full per-metric diagnostics in `diagnostics.json`. Machine-readable results in `metric_results.parquet`.
