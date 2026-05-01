# Result card — abct_fed_funds_below_taylor_rule_capital_misallocation_2002_2007

**Verdict:** inconclusive (data gaps)

**Reason:** 2 metrics met, 3 pending; 2 more need resolution

Pre-registered rule: SUPPORT if >= 4 of 5 metrics met; REFUTE if <= 2 met (impossible to hit support).

**Counts:** 2 MET · 0 NOT_MET · 3 PENDING_DATA · 0 PENDING_EVAL

**Primary country:** USA

## Metric-by-metric

| # | Metric | Status | Observed | Threshold | Notes |
|---|---|:---:|---:|---|---|
| 1 | taylor_rule_average_deviation_2002_2007 | MET | 1.68e+04 (2007) [max_in_window_fallback] | `>= 150 bps below Taylor rule average` |  |
| 2 | residential_investment_share_peak_excess | PENDING_DATA |  | `>= 1.0 SD above 1990-2001 mean at peak` | No USA observations in window 2003-2006 |
| 3 | mortgage_debt_to_gdp_rise | MET | 103 (2007) [pct_increase_from_baseline] | `>= 25 percentage points increase` |  |
| 4 | case_shiller_real_price_rise | PENDING_DATA |  | `>= 60% cumulative real growth` | No usable vintage for: shiller:us_home_price_real |
| 5 | post_bust_home_price_drawdown | PENDING_DATA |  | `>= 25% peak-to-trough decline` | No usable vintage for: shiller:us_home_price_real |

## Claim

> Between 2002 and 2007 the US effective Federal Funds Rate ran on average more than 200 basis points below the rate prescribed by a standard Taylor rule (1.5 inflation-gap, 0.5 output-gap weights, 2% natural rate). The 2008 housing bust and MBS write-downs constitute a canonical case of malinvestment in the inter-temporal capital structure: residential investment as a share of GDP rose 1.5 SD above its 1990-2001 mean, household mortgage debt rose by more than 40 percentage points of GDP, and the post-bust write-down of housing-sector capital exceeded $4 trillion. The Austrian interpretation — Greenspan-era loose money distorted the relative price of long-duration capital goods — is consistent with the multi-metric pattern of pre-bust extremes and post-bust collapse.

## Interpretation

Verdict is **inconclusive (data gaps)** — 3 metric(s) cannot be evaluated because the underlying data source is not yet in the vintages pipeline, and 0 metric(s) have data but a threshold expression the auto-evaluator does not recognise (complex conditions, discrete event counts, cross-country gaps). Close these gaps then re-run.

## Steelman live concerns

See `hypotheses/steelman/abct_fed_funds_below_taylor_rule_capital_misallocation_2002_2007.md` for the strongest opposing arguments. Canonical-case multi-metric evidence is a pattern match, not a causal identification — the result card should be read as 'outcome trajectory matches the predicted pattern to degree X' rather than 'policy P caused the outcome'.

## Provenance

Vintages pinned in `manifest.yaml`. Full per-metric diagnostics in `diagnostics.json`. Machine-readable results in `metric_results.parquet`.
