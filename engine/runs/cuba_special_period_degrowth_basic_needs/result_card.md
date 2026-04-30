# Result card — cuba_special_period_degrowth_basic_needs

**Verdict:** inconclusive (data gaps)

**Reason:** 1 metrics met, 3 pending; 3 more need resolution

Pre-registered rule: SUPPORT if >= 4 of 4 metrics met; REFUTE if <= 2 met (impossible to hit support).

**Counts:** 1 MET · 0 NOT_MET · 0 PENDING_DATA · 3 PENDING_EVAL

**Primary country:** CUB

## Metric-by-metric

| # | Metric | Status | Observed | Threshold | Notes |
|---|---|:---:|---:|---|---|
| 1 | gdp_pc_peak_to_trough_contraction | MET | 36.6 (1993) [peak_to_trough_pct_decline] | `>=25% real GDP per capita decline from 1989 peak to 1991-1995 trough` |  |
| 2 | life_expectancy_preserved | PENDING_EVAL | 2.85 (1991) [peak_to_trough_pct_decline] | `max(LE_1989 - LE_t for t in 1990..2000) / LE_1989 <= 0.10` | threshold expression unparseable by regex |
| 3 | infant_mortality_preserved | PENDING_EVAL | 37 (2000) [peak_to_trough_pct_decline] | `max(IMR_t / IMR_1989 for t in 1990..2000) <= 1.10` | threshold expression unparseable by regex |
| 4 | primary_school_enrolment_preserved | PENDING_EVAL | 4.46 (1995) [peak_to_trough_pct_decline] | `min(ENROL_t / ENROL_1989 for t in 1990..2000) >= 0.90` | threshold expression unparseable by regex |

## Claim

> Cuban post-1991 Special Period forced degrowth (real GDP per capita contracted ~35% over 1989-1993 after the Soviet bloc collapse cut off concessional sugar/oil terms) demonstrated that basic-needs provision (life expectancy, infant mortality, primary-school enrolment) can be maintained — or improved — during rapid material-throughput reduction when institutions are aligned around free universal health and education.

## Interpretation

Verdict is **inconclusive (data gaps)** — 0 metric(s) cannot be evaluated because the underlying data source is not yet in the vintages pipeline, and 3 metric(s) have data but a threshold expression the auto-evaluator does not recognise (complex conditions, discrete event counts, cross-country gaps). Close these gaps then re-run.

## Steelman live concerns

See `hypotheses/steelman/cuba_special_period_degrowth_basic_needs.md` for the strongest opposing arguments. Canonical-case multi-metric evidence is a pattern match, not a causal identification — the result card should be read as 'outcome trajectory matches the predicted pattern to degree X' rather than 'policy P caused the outcome'.

## Provenance

Vintages pinned in `manifest.yaml`. Full per-metric diagnostics in `diagnostics.json`. Machine-readable results in `metric_results.parquet`.
