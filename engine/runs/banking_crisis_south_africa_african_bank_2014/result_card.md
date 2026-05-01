# Result card — banking_crisis_south_africa_african_bank_2014

**Verdict:** supported

**Reason:** 4 of 4 metrics met threshold (support threshold 3)

Pre-registered rule: SUPPORT if >= 3 of 4 metrics met; REFUTE if <= 1 met (impossible to hit support).

**Counts:** 4 MET · 0 NOT_MET · 0 PENDING_DATA · 0 PENDING_EVAL

**Primary country:** ZAF

## Metric-by-metric

| # | Metric | Status | Observed | Threshold | Notes |
|---|---|:---:|---:|---|---|
| 1 | african_bank_curatorship_2014 | MET | 1 (2014) [yes_no_indicator_max] | `yes/no — yes counts as breach` | yes/no event evaluated from binary event indicator |
| 2 | good_bank_bad_bank_split | MET | 1 (2016) [yes_no_indicator_max] | `yes/no — yes counts as breach` | yes/no event evaluated from binary event indicator |
| 3 | laeven_valencia_no_systemic_coding | MET | 0 (2014) [coded_no_indicator_max] | `coded NO — supports the contained-resolution framing` | coded NO evaluated from binary event indicator |
| 4 | real_gdp_undisturbed | MET | 1.32 (2015) [annual_growth_rate_value] | `annual growth >= 1% in each of 2014 and 2015` | annual growth values: 2014=1.414, 2015=1.322; threshold each >=1 |

## Claim

> South Africa's August 2014 African Bank Limited curatorship — SARB-led resolution of an unsecured-consumer-credit lender, retail-deposit guarantee, good-bank / bad-bank split, no propagation to systemic banks (Standard Bank, FirstRand, Absa, Nedbank) — is a canonical case of a contained-resolution single-institution failure in an emerging market with an effective supervisory framework. The hypothesis is that South Africa 2014 meets a deliberately-narrow checklist on at least 3 of 4 metrics WITHOUT producing a Laeven-Valencia coded systemic crisis or material macro impact.

## Interpretation

The canonical-case pattern match is satisfied: 4 of 4 pre-registered metrics meet their thresholds, above the support threshold of 3. Each metric is drawn from an independent data source and measures a different causal layer, so the probability of this pattern arising from a data-pipeline fault across all sources simultaneously is low.

## Steelman live concerns

See `hypotheses/steelman/banking_crisis_south_africa_african_bank_2014.md` for the strongest opposing arguments. Canonical-case multi-metric evidence is a pattern match, not a causal identification — the result card should be read as 'outcome trajectory matches the predicted pattern to degree X' rather than 'policy P caused the outcome'.

## Provenance

Vintages pinned in `manifest.yaml`. Full per-metric diagnostics in `diagnostics.json`. Machine-readable results in `metric_results.parquet`.
