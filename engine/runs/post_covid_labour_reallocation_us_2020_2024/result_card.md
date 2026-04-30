# Result card — post_covid_labour_reallocation_us_2020_2024

**Verdict:** inconclusive (data gaps)

**Reason:** 0 metrics met, 5 pending; 4 more need resolution

Pre-registered rule: SUPPORT if >= 4 of 5 metrics met; REFUTE if <= 2 met (impossible to hit support).

**Counts:** 0 MET · 0 NOT_MET · 5 PENDING_DATA · 0 PENDING_EVAL

**Primary country:** USA

## Metric-by-metric

| # | Metric | Status | Observed | Threshold | Notes |
|---|---|:---:|---:|---|---|
| 1 | leisure_hospitality_employment_collapse_2020 | PENDING_DATA |  | `>35% decline peak-to-trough` | No usable vintage for: fred:USLAH |
| 2 | leisure_hospitality_wage_overrecovery_2024 | PENDING_DATA |  | `>5pp cumulative excess over aggregate private AHE 2019-12 to 2024-12` | No usable vintage for: fred:CES7000000003, fred:CES0500000003 |
| 3 | information_sector_employment_recovery | PENDING_DATA |  | `by 2024-12 employment >= 2019-12 level (full recovery or above)` | No usable vintage for: fred:USINFO |
| 4 | wfh_share_persistence_2024 | PENDING_DATA |  | `>25% of full-time employees still hybrid or fully remote in 2024` | No usable vintage for: bls:american_time_use_survey_telework |
| 5 | retail_brick_mortar_employment_shortfall | PENDING_DATA |  | `by 2024-12 employment <= 95% of 2019-12 level` | No usable vintage for: fred:CES4245200001 |

## Claim

> The US COVID labour-market shock 2020-2024 produced a sharp asymmetric reallocation — leisure/hospitality and brick-and-mortar retail collapsed in 2020 then over-recovered nominal wages relative to trend, while professional/information sectors saw remote-work entrenchment with persistently elevated WFH share and lower CBD office utilisation through 2024.

## Interpretation

Verdict is **inconclusive (data gaps)** — 5 metric(s) cannot be evaluated because the underlying data source is not yet in the vintages pipeline, and 0 metric(s) have data but a threshold expression the auto-evaluator does not recognise (complex conditions, discrete event counts, cross-country gaps). Close these gaps then re-run.

## Steelman live concerns

See `hypotheses/steelman/post_covid_labour_reallocation_us_2020_2024.md` for the strongest opposing arguments. Canonical-case multi-metric evidence is a pattern match, not a causal identification — the result card should be read as 'outcome trajectory matches the predicted pattern to degree X' rather than 'policy P caused the outcome'.

## Provenance

Vintages pinned in `manifest.yaml`. Full per-metric diagnostics in `diagnostics.json`. Machine-readable results in `metric_results.parquet`.
