# Result card — japan_zero_growth_basic_wellbeing_intact

**Verdict:** inconclusive (data gaps)

**Reason:** 0 metrics met, 4 pending; 4 more need resolution

Pre-registered rule: SUPPORT if >= 4 of 4 metrics met; REFUTE if <= 2 met (impossible to hit support).

**Counts:** 0 MET · 0 NOT_MET · 0 PENDING_DATA · 4 PENDING_EVAL

**Primary country:** JPN

## Metric-by-metric

| # | Metric | Status | Observed | Threshold | Notes |
|---|---|:---:|---:|---|---|
| 1 | jpn_zero_growth_premise | PENDING_EVAL | 0 (1990) [pct_increase_from_baseline] | `mean(NY.GDP.PCAP.KD.ZG, 1990-2019) < 1.5%` | threshold expression unparseable by regex |
| 2 | jpn_life_expectancy_gain | PENDING_EVAL | 7 (2019) [pct_increase_from_baseline] | `LE_2019 - LE_1990 >= 4 years` | threshold expression unparseable by regex |
| 3 | jpn_hours_worked_decline | PENDING_EVAL | 0 (1990) [pct_increase_from_baseline] | `avh_2019 / avh_1990 <= 0.90` | threshold expression unparseable by regex |
| 4 | jpn_life_satisfaction_stable_oecd_median | PENDING_EVAL |  | `max(|cantril_jpn_t - cantril_oecd_median_t|) <= 1.0 over 2008-2020` | Non-tidy (needs custom parser): owid:happiness-cantril-ladder |

## Claim

> Japan's 1990-2020 near-zero per-capita GDP growth regime (mean GDP/capita growth < 1%) coincided with a meaningful improvement in life expectancy at birth (+5 years), a sharp decline in average annual hours worked per employed person (~-15%), and a stable Cantril life-satisfaction trajectory at OECD-median levels. The pattern refutes the proposition that per-capita GDP growth is a binding constraint on retaining or improving baseline-wellbeing outcomes in advanced economies.

## Interpretation

Verdict is **inconclusive (data gaps)** — 0 metric(s) cannot be evaluated because the underlying data source is not yet in the vintages pipeline, and 4 metric(s) have data but a threshold expression the auto-evaluator does not recognise (complex conditions, discrete event counts, cross-country gaps). Close these gaps then re-run.

## Steelman live concerns

See `hypotheses/steelman/japan_zero_growth_basic_wellbeing_intact.md` for the strongest opposing arguments. Canonical-case multi-metric evidence is a pattern match, not a causal identification — the result card should be read as 'outcome trajectory matches the predicted pattern to degree X' rather than 'policy P caused the outcome'.

## Provenance

Vintages pinned in `manifest.yaml`. Full per-metric diagnostics in `diagnostics.json`. Machine-readable results in `metric_results.parquet`.
