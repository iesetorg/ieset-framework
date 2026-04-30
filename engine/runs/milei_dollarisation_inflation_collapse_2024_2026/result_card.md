# Result card — milei_dollarisation_inflation_collapse_2024_2026

**Verdict:** inconclusive (data gaps)

**Reason:** 0 metrics met, 5 pending; 4 more need resolution

Pre-registered rule: SUPPORT if >= 4 of 5 metrics met; REFUTE if <= 2 met (impossible to hit support).

**Counts:** 0 MET · 0 NOT_MET · 4 PENDING_DATA · 1 PENDING_EVAL

**Primary country:** ARG

## Metric-by-metric

| # | Metric | Status | Observed | Threshold | Notes |
|---|---|:---:|---:|---|---|
| 1 | monthly_inflation_collapse | PENDING_DATA |  | `monthly inflation < 3% by Dec 2025; sustained < 4% for 6+ months` | No usable vintage for: bcra:inflation_monthly, indec:ipc_monthly |
| 2 | primary_fiscal_surplus_achieved | PENDING_EVAL | 0.5 (2024) [max_in_window_fallback] | `primary balance > 0% of GDP in 2024 AND 2025` | threshold expression unparseable by regex |
| 3 | parallel_fx_gap_compression | PENDING_DATA |  | `parallel_fx_gap < 0.20 by Dec 2025` | No usable vintage for: bcra:fx_official, dolartoday:blue_rate |
| 4 | output_recession_bounded | PENDING_DATA |  | `max peak_to_trough log_real_gdp decline < 0.04` | No usable vintage for: imf:NGDP_R, indec:emae |
| 5 | poverty_rate_recovery | PENDING_DATA |  | `INDEC poverty headcount < 42% by 2026-S1` | No usable vintage for: indec:eph_pobreza |

## Claim

> Argentina under Milei (December 2023 inauguration) executed a fiscal-surplus + monetary-contraction + de-facto-dollarisation programme that collapsed monthly CPI inflation from ~25% (Dec 2023) toward sub-3% by 2025-2026, eliminated the primary fiscal deficit within a single fiscal year, and compressed the parallel-market peso-USD gap (blue-dolar / official) from over 100% to near zero. The pre-registered claim is that across four monetary/fiscal metrics — monthly inflation, primary fiscal balance, peso-USD parallel-market gap, and BCRA real monetary base — the Milei programme produces extreme outcomes that diverge from prior Argentine stabilisation attempts (Convertibilidad 1991, Macri 2015-2019) and from Latin American disinflation comparators. The headline test is whether the inflation collapse holds without a recession of comparable magnitude to the disinflation gain (output decline less than 4% peak-to-trough).

## Interpretation

Verdict is **inconclusive (data gaps)** — 4 metric(s) cannot be evaluated because the underlying data source is not yet in the vintages pipeline, and 1 metric(s) have data but a threshold expression the auto-evaluator does not recognise (complex conditions, discrete event counts, cross-country gaps). Close these gaps then re-run.

## Steelman live concerns

See `hypotheses/steelman/milei_dollarisation_inflation_collapse_2024_2026.md` for the strongest opposing arguments. Canonical-case multi-metric evidence is a pattern match, not a causal identification — the result card should be read as 'outcome trajectory matches the predicted pattern to degree X' rather than 'policy P caused the outcome'.

## Provenance

Vintages pinned in `manifest.yaml`. Full per-metric diagnostics in `diagnostics.json`. Machine-readable results in `metric_results.parquet`.
