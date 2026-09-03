# Result card — banking_crisis_greece_2010_2018_doom_loop

**Verdict:** supported

> **QUARANTINED pending v2 re-score — adversarial audit remediation 2026-09-03.** See the Correction section below before citing this card. Primary finding: X1/X2: unemployment '>=19 pp rise' scored against pct_increase_from_baseline = 1.43e+03; government debt '>=175% of GDP' against max_in_window_fallback = 4.94e+04.


**Reason:** 6 of 6 metrics met threshold (support threshold 5)

Pre-registered rule: SUPPORT if >= 5 of 6 metrics met; REFUTE if <= 2 met (impossible to hit support).

## Correction 2026-09-03 — adversarial audit remediation

**Disposition:** QUARANTINED pending v2 re-score · **Audit:** `engine/audits/ieset_adversarial_supported_claims_2026-07-31.md` (claim 15) · **Remediation:** `engine/audits/ieset_adversarial_audit_remediation_2026-09-03.md` · **Detectors:** `scripts/audit_integrity_detectors.py`

- X1/X2: unemployment '>=19 pp rise' scored against pct_increase_from_baseline = 1.43e+03; government debt '>=175% of GDP' against max_in_window_fallback = 4.94e+04 — sentinel/wrong-series artefacts scored MET.
- The doom-loop propagation mechanism is untested: six co-occurring state variables, no exposure or sequencing metric.

**Machine-detector confirmations in diagnostics.json (not counted toward the verdict pending v2):**
- metric `unemployment_peak` [sentinel_value]: percent-change stat at 1427.2739 >= 99.99 — fallback/sentinel artefact, not a real observation
- metric `government_debt_peak` [sentinel_value]: value 4.942e+04 at >=1e4 scale for percent/ratio-family stat 'max_in_window_fallback' — wrong series or sentinel scored as MET
- metric `unemployment_peak` [unit_typetag_mismatch]: threshold in percentage_points evaluated against percent-change stat 'pct_increase_from_baseline' — MET/NOT_MET mechanically manufactured

No original content has been deleted; this correction is additive.

**Counts:** 6 MET · 0 NOT_MET · 0 PENDING_DATA · 0 PENDING_EVAL

**Primary country:** GRC

## Metric-by-metric

| # | Metric | Status | Observed | Threshold | Notes |
|---|---|:---:|---:|---|---|
| 1 | real_gdp_peak_to_trough | MET | 27 (2013) [peak_to_trough_pct_decline] | `>= 25% decline` |  |
| 2 | unemployment_peak | MET | 1.43e+03 (2013) [pct_increase_from_baseline] | `>= 19 pp rise (peak >= 27%)` |  |
| 3 | government_debt_peak | MET | 4.94e+04 (2011) [max_in_window_fallback] | `>= 175% of GDP` |  |
| 4 | psi_sovereign_restructuring_2012 | MET | 1 (2012) [yes_no_indicator_max] | `yes/no — yes counts as breach` | yes/no event evaluated from binary event indicator |
| 5 | capital_controls_imposed_2015 | MET | 1 (2015) [yes_no_indicator_max] | `yes/no — yes counts as breach` | yes/no event evaluated from binary event indicator |
| 6 | bank_npl_ratio_peak | MET | 46 (2017) [max_in_window_fallback] | `>= 40% of gross loans` |  |

## Claim

> Greece 2010-2018 exhibits the canonical sovereign-banking doom-loop: sovereign-debt distress propagated through bank holdings of Greek government bonds, requiring three successive IMF/EU programmes (2010, 2012, 2015), a sovereign restructuring in 2012 (PSI), and bank recapitalisations that depressed real GDP cumulatively by >= 25% peak-to-trough. The hypothesis is that the canonical multi-metric signature for Greece is met across at least 5 of 6 metrics.

## Interpretation

The canonical-case pattern match is satisfied: 6 of 6 pre-registered metrics meet their thresholds, above the support threshold of 5. Each metric is drawn from an independent data source and measures a different causal layer, so the probability of this pattern arising from a data-pipeline fault across all sources simultaneously is low.

## Steelman live concerns

See `hypotheses/steelman/banking_crisis_greece_2010_2018_doom_loop.md` for the strongest opposing arguments. Canonical-case multi-metric evidence is a pattern match, not a causal identification — the result card should be read as 'outcome trajectory matches the predicted pattern to degree X' rather than 'policy P caused the outcome'.

## Provenance

Vintages pinned in `manifest.yaml`. Full per-metric diagnostics in `diagnostics.json`. Machine-readable results in `metric_results.parquet`.
