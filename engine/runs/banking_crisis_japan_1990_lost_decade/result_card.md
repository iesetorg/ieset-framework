# Result card — banking_crisis_japan_1990_lost_decade

**Verdict:** supported

**Reason:** 4 of 5 metrics met threshold (support threshold 4)

Pre-registered rule: SUPPORT if >= 4 of 5 metrics met; REFUTE if <= 1 met (impossible to hit support).

**Counts:** 4 MET · 0 NOT_MET · 1 PENDING_DATA · 0 PENDING_EVAL

**Primary country:** JPN

## Metric-by-metric

| # | Metric | Status | Observed | Threshold | Notes |
|---|---|:---:|---:|---|---|
| 1 | equity_index_decline | MET | 72.7 (2003) [peak_to_trough_pct_decline] | `>= 60% peak-to-trough decline (Dec-1989 to Apr-2003)` |  |
| 2 | real_house_price_decline | MET | 46 (2005) [peak_to_trough_pct_decline] | `>= 40% decline` |  |
| 3 | real_gdp_growth_lost_decade | MET | 0.896 (2002) [average_annual_growth_rate_value] | `<= 1% average annual growth` | average annual growth 1992-2002 = 0.896; threshold <=1 |
| 4 | laeven_valencia_systemic_banking_crisis | MET | 1 (1997) [coded_yes_indicator_max] | `coded yes in 1997-2001 (Laeven-Valencia codes Japan 1997-2001)` | coded YES evaluated from binary event indicator |
| 5 | bank_npl_ratio_peak | PENDING_DATA |  | `>= 8% of gross loans` | No JPN observations in window 1998-2003 |

## Claim

> Japan's 1990-2003 banking-and-asset-bubble bust — Nikkei index decline of >= 60% peak-to-trough, real residential property price decline of >= 40%, persistent bank-NPL accumulation that required government recapitalisation in 1998 and 2003, and a "lost decade" of GDP growth averaging <= 1% — is a canonical case of a delayed-resolution banking crisis. The hypothesis is that Japan 1990-2003 meets the canonical multi-metric checklist on at least 4 of 5 metrics.

## Interpretation

The canonical-case pattern match is satisfied: 4 of 5 pre-registered metrics meet their thresholds, above the support threshold of 4. Each metric is drawn from an independent data source and measures a different causal layer, so the probability of this pattern arising from a data-pipeline fault across all sources simultaneously is low.

## Steelman live concerns

See `hypotheses/steelman/banking_crisis_japan_1990_lost_decade.md` for the strongest opposing arguments. Canonical-case multi-metric evidence is a pattern match, not a causal identification — the result card should be read as 'outcome trajectory matches the predicted pattern to degree X' rather than 'policy P caused the outcome'.

## Provenance

Vintages pinned in `manifest.yaml`. Full per-metric diagnostics in `diagnostics.json`. Machine-readable results in `metric_results.parquet`.
