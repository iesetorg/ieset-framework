# Result card — banking_crisis_italy_2016_2017_mps

**Verdict:** inconclusive (data gaps)

**Reason:** 1 metrics met, 3 pending; 2 more need resolution

Pre-registered rule: SUPPORT if >= 3 of 4 metrics met; REFUTE if <= 1 met (impossible to hit support).

**Counts:** 1 MET · 0 NOT_MET · 3 PENDING_DATA · 0 PENDING_EVAL

**Primary country:** ITA

## Metric-by-metric

| # | Metric | Status | Observed | Threshold | Notes |
|---|---|:---:|---:|---|---|
| 1 | bank_npl_ratio_peak | PENDING_DATA |  | `>= 16% gross NPL ratio` | No usable vintage for: world_bank_wdi:FB.AST.NPER.ZS, ecb:CBD2 |
| 2 | mps_precautionary_recap | PENDING_DATA |  | `yes/no — yes counts as breach` | No usable vintage for: ecb:MPS_PRECAUTIONARY_RECAP_2017 |
| 3 | veneto_banks_resolution | PENDING_DATA |  | `yes/no — yes counts as breach` | No usable vintage for: ecb:VENETO_BANKS_RESOLUTION_2017 |
| 4 | bank_credit_to_gdp_decline | MET | 18.3 (2018) [peak_to_trough_pct_decline] | `>= 15 pp of GDP decline` |  |

## Claim

> Italy's 2016-2017 banking-distress episode — Banca Monte dei Paschi di Siena precautionary recapitalisation in July 2017, Veneto-banks resolution in June 2017, and a peak system-wide non-performing-loan ratio above 17% — represents a protracted-NPL-overhang post-GFC banking distress case that did NOT meet the canonical full-systemic-banking-crisis threshold but DID require multiple state-aid resolution events. The hypothesis is that Italy 2016-2017 meets a deliberately- weaker multi-metric checklist on at least 3 of 4 metrics, while explicitly NOT meeting the full Laeven-Valencia systemic-crisis threshold.

## Interpretation

Verdict is **inconclusive (data gaps)** — 3 metric(s) cannot be evaluated because the underlying data source is not yet in the vintages pipeline, and 0 metric(s) have data but a threshold expression the auto-evaluator does not recognise (complex conditions, discrete event counts, cross-country gaps). Close these gaps then re-run.

## Steelman live concerns

See `hypotheses/steelman/banking_crisis_italy_2016_2017_mps.md` for the strongest opposing arguments. Canonical-case multi-metric evidence is a pattern match, not a causal identification — the result card should be read as 'outcome trajectory matches the predicted pattern to degree X' rather than 'policy P caused the outcome'.

## Provenance

Vintages pinned in `manifest.yaml`. Full per-metric diagnostics in `diagnostics.json`. Machine-readable results in `metric_results.parquet`.
