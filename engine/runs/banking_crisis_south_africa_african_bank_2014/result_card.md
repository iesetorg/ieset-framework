# Result card — banking_crisis_south_africa_african_bank_2014

**Verdict:** inconclusive (data gaps)

**Reason:** 0 metrics met, 4 pending; 3 more need resolution

Pre-registered rule: SUPPORT if >= 3 of 4 metrics met; REFUTE if <= 1 met (impossible to hit support).

**Counts:** 0 MET · 0 NOT_MET · 3 PENDING_DATA · 1 PENDING_EVAL

**Primary country:** ZAF

## Metric-by-metric

| # | Metric | Status | Observed | Threshold | Notes |
|---|---|:---:|---:|---|---|
| 1 | african_bank_curatorship_2014 | PENDING_DATA |  | `yes/no — yes counts as breach` | No usable vintage for: imf:ZAF_AFRICAN_BANK_2014 |
| 2 | good_bank_bad_bank_split | PENDING_DATA |  | `yes/no — yes counts as breach` | No usable vintage for: imf:ZAF_GBBB_2014 |
| 3 | laeven_valencia_no_systemic_coding | PENDING_DATA |  | `coded NO — supports the contained-resolution framing` | No usable vintage for: owid:systemic-banking-crises |
| 4 | real_gdp_undisturbed | PENDING_EVAL | 0 (2014) [pct_increase_from_baseline] | `annual growth >= 1% in each of 2014 and 2015` | threshold expression unparseable by regex |

## Claim

> South Africa's August 2014 African Bank Limited curatorship — SARB-led resolution of an unsecured-consumer-credit lender, retail-deposit guarantee, good-bank / bad-bank split, no propagation to systemic banks (Standard Bank, FirstRand, Absa, Nedbank) — is a canonical case of a contained-resolution single-institution failure in an emerging market with an effective supervisory framework. The hypothesis is that South Africa 2014 meets a deliberately-narrow checklist on at least 3 of 4 metrics WITHOUT producing a Laeven-Valencia coded systemic crisis or material macro impact.

## Interpretation

Verdict is **inconclusive (data gaps)** — 3 metric(s) cannot be evaluated because the underlying data source is not yet in the vintages pipeline, and 1 metric(s) have data but a threshold expression the auto-evaluator does not recognise (complex conditions, discrete event counts, cross-country gaps). Close these gaps then re-run.

## Steelman live concerns

See `hypotheses/steelman/banking_crisis_south_africa_african_bank_2014.md` for the strongest opposing arguments. Canonical-case multi-metric evidence is a pattern match, not a causal identification — the result card should be read as 'outcome trajectory matches the predicted pattern to degree X' rather than 'policy P caused the outcome'.

## Provenance

Vintages pinned in `manifest.yaml`. Full per-metric diagnostics in `diagnostics.json`. Machine-readable results in `metric_results.parquet`.
