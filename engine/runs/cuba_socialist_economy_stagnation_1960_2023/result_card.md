# Result card — cuba_socialist_economy_stagnation_1960_2023

**Verdict:** supported

**Reason:** 7 of 10 metrics met threshold (support threshold 7)

Pre-registered rule: SUPPORT if >= 7 of 10 metrics met; REFUTE if <= 3 met (impossible to hit support).

**Counts:** 7 MET · 3 NOT_MET · 0 PENDING_DATA · 0 PENDING_EVAL

**Primary country:** CUB

## Metric-by-metric

| # | Metric | Status | Observed | Threshold | Notes |
|---|---|:---:|---:|---|---|
| 1 | gdp_per_capita_divergence_vs_latam | NOT_MET |  | `CUB 2023 GDP pc / CUB 1960 GDP pc < 1.5 AND LatAm peer median 2023/1960 ratio > 3.0` | CUB 2023/1960 ratio = 2.781 (used years 2018/1960); LatAm peer median 2023/1960 ratio = 2.916 (n=19) |
| 2 | gdp_per_capita_rank_reversal_latam | NOT_MET |  | `CUB rank in top 5 (1958) AND CUB rank in bottom 10 out of 20 LatAm (2023)` | CUB rank in 1958 = 73 (top 5 required); CUB rank in 2023 = 15/19 (bottom 10 requires rank >= 10) |
| 3 | special_period_contraction_1989_1993 | MET | 100 (1993) [peak_to_trough_pct_decline] | `>25% cumulative real GDP contraction 1989-1993` |  |
| 4 | emigration_share_population_cumulative | MET | 2.4e+06 (2023) [max_in_window] | `>15% of 2023 notional population (residents + diaspora) living abroad` |  |
| 5 | agricultural_self_sufficiency_collapse | MET |  | `>60% of food supply imported by caloric value in any year 2015-2023` | event-count [max_value] = 80 in 2015-2023; threshold >60 |
| 6 | ration_card_persistence | MET | 63 (2024) [max_in_window] | `>49 years of continuous national libreta system in force in any year of the window` |  |
| 7 | private_sector_share_employment | MET | 54 (2023) [max_in_window] | `>39 years in any year of the window with private sector employment share below 25%` |  |
| 8 | currency_dual_system_dysfunction | MET |  | `>1 major monetary-regime changes (redenomination, FX-regime switch, or 100%+ annualised inflation episode) during 1993-2023` | event-count [max_cumulative] = 4 in 1993-2023; threshold >1 |
| 9 | hdi_stagnation_relative | NOT_MET |  | `CUB HDI 2022 - CUB HDI 1990 < 0.03 AND LatAm peer median HDI 2022 - 1990 > 0.10` | CUB 2022-1990 diff = 0.077 (used 2022, 1990); LatAm peer median 2022-1990 diff = 0.146 (n=19) |
| 10 | informal_dollarisation_2020s | MET | 6 (2024) [max_in_window] | `>1 years in any year of documented state-sanctioned USD-only retail network covering staple goods` |  |

## Claim

> Cuba's post-1959 socialist policy regime (Castro 1959-2008 + Raúl 2008-2018 + Díaz-Canel 2018-present, characterised by single-party rule, state ownership of most productive assets, ration-card consumption, FX duality, and chronic suppression of private enterprise) produced a canonical 60-year material stagnation that manifests as ≥7 of 10 pre-registered extreme-outcome metrics, each drawn from an independent data source and measuring a different causal layer. Unlike Venezuela or Zimbabwe — which are episodic collapses — Cuba's pattern is persistent-state stagnation punctuated by the 1989-1993 Special Period. The canonical-case claim is that no non-war Latin American peer in the 1960-2023 window matches even 4 of these 10 thresholds simultaneously; Cuba matches most. A refutation (≤3 metrics met) would indicate that the framework's institutional- quality coding of Cuba is overstated, that Cuba's material- welfare gap versus peer LatAm has been systematically mismeasured, or that US embargo effects dominate the institutional channel.

## Interpretation

The canonical-case pattern match is satisfied: 7 of 10 pre-registered metrics meet their thresholds, above the support threshold of 7. Each metric is drawn from an independent data source and measures a different causal layer, so the probability of this pattern arising from a data-pipeline fault across all sources simultaneously is low.

## Steelman live concerns

See `hypotheses/steelman/cuba_socialist_economy_stagnation_1960_2023.md` for the strongest opposing arguments. Canonical-case multi-metric evidence is a pattern match, not a causal identification — the result card should be read as 'outcome trajectory matches the predicted pattern to degree X' rather than 'policy P caused the outcome'.

## Provenance

Vintages pinned in `manifest.yaml`. Full per-metric diagnostics in `diagnostics.json`. Machine-readable results in `metric_results.parquet`.
