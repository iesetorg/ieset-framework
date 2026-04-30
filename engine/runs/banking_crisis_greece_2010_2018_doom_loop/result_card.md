# Result card — banking_crisis_greece_2010_2018_doom_loop

**Verdict:** inconclusive (data gaps)

**Reason:** 2 metrics met, 4 pending; 3 more need resolution

Pre-registered rule: SUPPORT if >= 5 of 6 metrics met; REFUTE if <= 2 met (impossible to hit support).

**Counts:** 2 MET · 0 NOT_MET · 3 PENDING_DATA · 1 PENDING_EVAL

**Primary country:** GRC

## Metric-by-metric

| # | Metric | Status | Observed | Threshold | Notes |
|---|---|:---:|---:|---|---|
| 1 | real_gdp_peak_to_trough | MET | 27 (2013) [peak_to_trough_pct_decline] | `>= 25% decline` |  |
| 2 | unemployment_peak | MET | 118 (2013) [pct_increase_from_baseline] | `>= 19 pp rise (peak >= 27%)` |  |
| 3 | government_debt_peak | PENDING_EVAL | 190 [max_loaded_value] | `>= 175% of GDP` | count-based threshold requires event log; data not sufficient to auto-count |
| 4 | psi_sovereign_restructuring_2012 | PENDING_DATA |  | `yes/no — yes counts as breach` | No usable vintage for: imf:EFF_GRC_2012 |
| 5 | capital_controls_imposed_2015 | PENDING_DATA |  | `yes/no — yes counts as breach` | No usable vintage for: imf:GRC_CFM_2015 |
| 6 | bank_npl_ratio_peak | PENDING_DATA |  | `>= 40% of gross loans` | No usable vintage for: world_bank_wdi:FB.AST.NPER.ZS |

## Claim

> Greece 2010-2018 exhibits the canonical sovereign-banking doom-loop: sovereign-debt distress propagated through bank holdings of Greek government bonds, requiring three successive IMF/EU programmes (2010, 2012, 2015), a sovereign restructuring in 2012 (PSI), and bank recapitalisations that depressed real GDP cumulatively by >= 25% peak-to-trough. The hypothesis is that the canonical multi-metric signature for Greece is met across at least 5 of 6 metrics.

## Interpretation

Verdict is **inconclusive (data gaps)** — 3 metric(s) cannot be evaluated because the underlying data source is not yet in the vintages pipeline, and 1 metric(s) have data but a threshold expression the auto-evaluator does not recognise (complex conditions, discrete event counts, cross-country gaps). Close these gaps then re-run.

## Steelman live concerns

See `hypotheses/steelman/banking_crisis_greece_2010_2018_doom_loop.md` for the strongest opposing arguments. Canonical-case multi-metric evidence is a pattern match, not a causal identification — the result card should be read as 'outcome trajectory matches the predicted pattern to degree X' rather than 'policy P caused the outcome'.

## Provenance

Vintages pinned in `manifest.yaml`. Full per-metric diagnostics in `diagnostics.json`. Machine-readable results in `metric_results.parquet`.
