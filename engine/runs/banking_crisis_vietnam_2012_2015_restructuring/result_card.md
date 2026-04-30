# Result card — banking_crisis_vietnam_2012_2015_restructuring

**Verdict:** inconclusive (data gaps)

**Reason:** 0 metrics met, 4 pending; 3 more need resolution

Pre-registered rule: SUPPORT if >= 3 of 4 metrics met; REFUTE if <= 1 met (impossible to hit support).

**Counts:** 0 MET · 0 NOT_MET · 3 PENDING_DATA · 1 PENDING_EVAL

**Primary country:** VNM

## Metric-by-metric

| # | Metric | Status | Observed | Threshold | Notes |
|---|---|:---:|---:|---|---|
| 1 | bank_npl_ratio_peak | PENDING_DATA |  | `>= 4% reported NPL ratio` | No usable vintage for: world_bank_wdi:FB.AST.NPER.ZS |
| 2 | vamc_created_2013 | PENDING_DATA |  | `yes/no — yes counts as breach` | No usable vintage for: imf:VNM_VAMC_2013 |
| 3 | zero_vnd_bank_acquisitions_2015 | PENDING_DATA |  | `yes/no — yes counts as breach` | No usable vintage for: imf:VNM_BANK_TAKEOVER_2015 |
| 4 | real_gdp_growth_undisturbed | PENDING_EVAL | 6.99 (2015) [max_in_window] | `annual growth >= 5% in each year (negative-control: contained restructuring)` | threshold expression unparseable by regex |

## Claim

> Vietnam's 2012-2015 banking-sector restructuring — Vietnam Asset Management Company (VAMC) created July 2013, NPL ratio peak above 4%, mandatory mergers of weak banks, and forced central-bank acquisition of three commercial banks at zero VND in 2015 — represents a controlled-resolution emerging-market banking distress event without a full systemic crisis. The hypothesis is that Vietnam 2012-2015 meets a deliberately- narrow multi-metric checklist on at least 3 of 4 metrics WITHOUT producing a Laeven-Valencia coded crisis or a real-GDP recession.

## Interpretation

Verdict is **inconclusive (data gaps)** — 3 metric(s) cannot be evaluated because the underlying data source is not yet in the vintages pipeline, and 1 metric(s) have data but a threshold expression the auto-evaluator does not recognise (complex conditions, discrete event counts, cross-country gaps). Close these gaps then re-run.

## Steelman live concerns

See `hypotheses/steelman/banking_crisis_vietnam_2012_2015_restructuring.md` for the strongest opposing arguments. Canonical-case multi-metric evidence is a pattern match, not a causal identification — the result card should be read as 'outcome trajectory matches the predicted pattern to degree X' rather than 'policy P caused the outcome'.

## Provenance

Vintages pinned in `manifest.yaml`. Full per-metric diagnostics in `diagnostics.json`. Machine-readable results in `metric_results.parquet`.
