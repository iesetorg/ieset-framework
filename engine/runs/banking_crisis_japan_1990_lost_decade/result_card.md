# Result card — banking_crisis_japan_1990_lost_decade

**Verdict:** inconclusive (data gaps)

**Reason:** 0 metrics met, 4 pending; 4 more need resolution

Pre-registered rule: SUPPORT if >= 4 of 5 metrics met; REFUTE if <= 1 met (impossible to hit support).

**Counts:** 0 MET · 1 NOT_MET · 4 PENDING_DATA · 0 PENDING_EVAL

**Primary country:** JPN

## Metric-by-metric

| # | Metric | Status | Observed | Threshold | Notes |
|---|---|:---:|---:|---|---|
| 1 | equity_index_decline | PENDING_DATA |  | `>= 60% peak-to-trough decline (Dec-1989 to Apr-2003)` | No usable vintage for: fred:NIKKEI225, jst:eq_tr |
| 2 | real_house_price_decline | PENDING_DATA |  | `>= 40% decline` | No usable vintage for: jst:hpnom; Non-tidy (needs custom parser): bis:WS_SPP |
| 3 | real_gdp_growth_lost_decade | NOT_MET | 248 (1996) [pct_increase_from_baseline] | `<= 1% average annual growth` |  |
| 4 | laeven_valencia_systemic_banking_crisis | PENDING_DATA |  | `coded yes in 1997-2001 (Laeven-Valencia codes Japan 1997-2001)` | No usable vintage for: owid:systemic-banking-crises |
| 5 | bank_npl_ratio_peak | PENDING_DATA |  | `>= 8% of gross loans` | No usable vintage for: world_bank_wdi:FB.AST.NPER.ZS |

## Claim

> Japan's 1990-2003 banking-and-asset-bubble bust — Nikkei index decline of >= 60% peak-to-trough, real residential property price decline of >= 40%, persistent bank-NPL accumulation that required government recapitalisation in 1998 and 2003, and a "lost decade" of GDP growth averaging <= 1% — is a canonical case of a delayed-resolution banking crisis. The hypothesis is that Japan 1990-2003 meets the canonical multi-metric checklist on at least 4 of 5 metrics.

## Interpretation

Verdict is **inconclusive (data gaps)** — 4 metric(s) cannot be evaluated because the underlying data source is not yet in the vintages pipeline, and 0 metric(s) have data but a threshold expression the auto-evaluator does not recognise (complex conditions, discrete event counts, cross-country gaps). Close these gaps then re-run.

## Steelman live concerns

See `hypotheses/steelman/banking_crisis_japan_1990_lost_decade.md` for the strongest opposing arguments. Canonical-case multi-metric evidence is a pattern match, not a causal identification — the result card should be read as 'outcome trajectory matches the predicted pattern to degree X' rather than 'policy P caused the outcome'.

## Provenance

Vintages pinned in `manifest.yaml`. Full per-metric diagnostics in `diagnostics.json`. Machine-readable results in `metric_results.parquet`.
