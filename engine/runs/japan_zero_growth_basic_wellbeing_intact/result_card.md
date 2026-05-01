# Result card — japan_zero_growth_basic_wellbeing_intact

**Verdict:** refuted

**Reason:** 1 metrics failed and 0 pending; cannot reach 4

Pre-registered rule: SUPPORT if >= 4 of 4 metrics met; REFUTE if <= 2 met (impossible to hit support).

**Counts:** 3 MET · 1 NOT_MET · 0 PENDING_DATA · 0 PENDING_EVAL

**Primary country:** JPN

## Metric-by-metric

| # | Metric | Status | Observed | Threshold | Notes |
|---|---|:---:|---:|---|---|
| 1 | jpn_zero_growth_premise | MET |  | `mean(NY.GDP.PCAP.KD.ZG, 1990-2019) < 1.5%` | JPN mean 1990-2019 = 0.961; threshold <1.5 |
| 2 | jpn_life_expectancy_gain | MET |  | `LE_2019 - LE_1990 >= 4 years` | JPN 2019-1990 diff = 5.519 (used 2019, 1990); threshold >=4 |
| 3 | jpn_hours_worked_decline | MET |  | `avh_2019 / avh_1990 <= 0.90` | JPN 2019/1990 ratio = 0.834 (used 2019, 1990); threshold <=0.9 |
| 4 | jpn_life_satisfaction_stable_oecd_median | NOT_MET |  | `max(|cantril_jpn_t - cantril_oecd_median_t|) <= 1.0 over 2008-2020` | max |JPN - OECD median| = 1.016 in 2019; threshold <=1 |

## Claim

> Japan's 1990-2020 near-zero per-capita GDP growth regime (mean GDP/capita growth < 1%) coincided with a meaningful improvement in life expectancy at birth (+5 years), a sharp decline in average annual hours worked per employed person (~-15%), and a stable Cantril life-satisfaction trajectory at OECD-median levels. The pattern refutes the proposition that per-capita GDP growth is a binding constraint on retaining or improving baseline-wellbeing outcomes in advanced economies.

## Interpretation

The canonical-case pattern match is not satisfied: only 3 of 4 metrics met their thresholds, below the support threshold of 4. Note that for canonical-case hypotheses, a refutation can indicate either that the hypothesis is genuinely weak, that the metric set is mis-calibrated (too strict), or that the data substrate has systematic gaps. Review the PENDING_DATA / PENDING_EVAL metrics before accepting the refutation.

## Steelman live concerns

See `hypotheses/steelman/japan_zero_growth_basic_wellbeing_intact.md` for the strongest opposing arguments. Canonical-case multi-metric evidence is a pattern match, not a causal identification — the result card should be read as 'outcome trajectory matches the predicted pattern to degree X' rather than 'policy P caused the outcome'.

## Provenance

Vintages pinned in `manifest.yaml`. Full per-metric diagnostics in `diagnostics.json`. Machine-readable results in `metric_results.parquet`.
