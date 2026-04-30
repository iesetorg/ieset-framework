# Result card — cuba_2021_protests_economic_reform_response

**Verdict:** inconclusive (data gaps)

**Reason:** 0 metrics met, 4 pending; 3 more need resolution

Pre-registered rule: SUPPORT if >= 3 of 4 metrics met; REFUTE if <= 1 met (impossible to hit support).

**Counts:** 0 MET · 0 NOT_MET · 4 PENDING_DATA · 0 PENDING_EVAL

**Primary country:** CUB

## Metric-by-metric

| # | Metric | Status | Observed | Threshold | Notes |
|---|---|:---:|---:|---|---|
| 1 | mipyme_formal_sector_expansion | PENDING_DATA |  | `registered_MIPYMEs > 9,000 cumulative by 2024-12-31` | No usable vintage for: cuba_manual:mipyme_registrations |
| 2 | real_wage_erosion_persistent | PENDING_DATA |  | `real_wage_index_2024 / real_wage_index_2019 < 0.60` | No usable vintage for: cuba_manual:salario_real |
| 3 | food_import_dependency_rising | PENDING_DATA |  | `(food_import_share_2023_2024 average) - (food_import_share_2019_2020 average) > 0.05` | No usable vintage for: faostat:fbs_import_share |
| 4 | emigration_outflow_unprecedented | PENDING_DATA |  | `cumulative_emigration_2022_2024 > 600,000` | No usable vintage for: uscbp:cuban_encounters, un_desa:cuban_migrant_stock |

## Claim

> Following the July 2021 protests (largest mass demonstrations in Cuba since 1959), the Cuban government enacted incremental economic reforms: legalisation of small/medium private enterprises (MIPYME, August 2021), partial dual-currency unification (Tarea Ordenamiento followed through), expansion of MLC (USD-denominated) retail circuits, and adjustment of official FX rates. The descriptive pre-registered claim is that across four metrics — registered MIPYMEs, real-wage purchasing power, food-import share of supply, and net emigration outflow — the post-2021 Cuban trajectory shows (a) a measurable expansion of the private-sector formal segment, (b) continued real-wage erosion despite reforms, (c) rising food-import dependency, and (d) the largest emigration outflow in Cuban history (>500k departures cumulative 2022-2024). The hypothesis tests whether reforms partially responded to social demands without restoring real living standards.

## Interpretation

Verdict is **inconclusive (data gaps)** — 4 metric(s) cannot be evaluated because the underlying data source is not yet in the vintages pipeline, and 0 metric(s) have data but a threshold expression the auto-evaluator does not recognise (complex conditions, discrete event counts, cross-country gaps). Close these gaps then re-run.

## Steelman live concerns

See `hypotheses/steelman/cuba_2021_protests_economic_reform_response.md` for the strongest opposing arguments. Canonical-case multi-metric evidence is a pattern match, not a causal identification — the result card should be read as 'outcome trajectory matches the predicted pattern to degree X' rather than 'policy P caused the outcome'.

## Provenance

Vintages pinned in `manifest.yaml`. Full per-metric diagnostics in `diagnostics.json`. Machine-readable results in `metric_results.parquet`.
