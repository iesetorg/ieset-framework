# Result card — asia_taiwan_tsmc_industrial_policy_1985_2024

**Verdict:** inconclusive (data gaps)

**Reason:** 0 metrics met, 6 pending; 4 more need resolution

Pre-registered rule: SUPPORT if >= 4 of 6 metrics met; REFUTE if <= 2 met (impossible to hit support).

**Counts:** 0 MET · 0 NOT_MET · 5 PENDING_DATA · 1 PENDING_EVAL

**Primary country:** TWN

## Metric-by-metric

| # | Metric | Status | Observed | Threshold | Notes |
|---|---|:---:|---:|---|---|
| 1 | manufacturing_va_share_persistent | PENDING_DATA |  | `manufacturing VA / GDP >= 30% in 2023` | No TWN observations in loaded vintages |
| 2 | rd_intensity_top_tier | PENDING_DATA |  | `R&D / GDP >= 3.5% in 2022` | No TWN observations in loaded vintages |
| 3 | high_tech_exports_share | PENDING_DATA |  | `>=60% high-tech share of manufactured exports in 2022` | No TWN observations in loaded vintages |
| 4 | gdp_pc_convergence_to_high_income | PENDING_DATA |  | `GDP-pc constant USD >= $30,000 in 2023` | No TWN observations in loaded vintages |
| 5 | tfp_growth_above_oecd | PENDING_EVAL | 95.3 (2019) [pct_increase_from_baseline] | `PWT rtfpna log-growth differential TWN minus OECD median >= 0.005/yr over 1985-2019` | threshold expression unparseable by regex |
| 6 | tsmc_global_share_dominance | PENDING_DATA |  | `Taiwan foundry share >= 60% world by 2023 (TSMC alone >50%)` | No usable vintage for: owid:semiconductor_industry |

## Claim

> Taiwan's semiconductor industrial policy — anchored by ITRI's 1980s technology incubation, the 1987 spin-off of TSMC under government ownership, the Hsinchu Science Park ecosystem, and sustained R&D-intensity targeting through 2024 — produced one of the largest industrial-policy successes in modern economic history. Taiwan's manufacturing value-added share of GDP remains above 30% through 2023 (vs OECD typical 12-18%); R&D / GDP exceeds 3.5% by 2022 (top-5 globally); high-tech exports / total manufacturing exports exceed 60% by 2022 (top-tier globally); and TFP index growth 1985-2019 exceeds OECD median by at least +0.5pp/yr.

## Interpretation

Verdict is **inconclusive (data gaps)** — 5 metric(s) cannot be evaluated because the underlying data source is not yet in the vintages pipeline, and 1 metric(s) have data but a threshold expression the auto-evaluator does not recognise (complex conditions, discrete event counts, cross-country gaps). Close these gaps then re-run.

## Steelman live concerns

See `hypotheses/steelman/asia_taiwan_tsmc_industrial_policy_1985_2024.md` for the strongest opposing arguments. Canonical-case multi-metric evidence is a pattern match, not a causal identification — the result card should be read as 'outcome trajectory matches the predicted pattern to degree X' rather than 'policy P caused the outcome'.

## Provenance

Vintages pinned in `manifest.yaml`. Full per-metric diagnostics in `diagnostics.json`. Machine-readable results in `metric_results.parquet`.
