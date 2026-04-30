# Result card — austrian_v_recovery_us_1920_no_fiscal_stim_canonical

**Verdict:** inconclusive (data gaps)

**Reason:** 0 metrics met, 5 pending; 4 more need resolution

Pre-registered rule: SUPPORT if >= 4 of 5 metrics met; REFUTE if <= 2 met (impossible to hit support).

**Counts:** 0 MET · 0 NOT_MET · 2 PENDING_DATA · 3 PENDING_EVAL

**Primary country:** USA

## Metric-by-metric

| # | Metric | Status | Observed | Threshold | Notes |
|---|---|:---:|---:|---|---|
| 1 | real_gdp_recovery_18mo | PENDING_DATA |  | `real_gdp(1923) >= real_gdp(1919)` | No usable vintage for: maddison:gdp_per_capita_2011usd |
| 2 | industrial_production_v_recovery | PENDING_EVAL |  | `>= 25% drop AND recovery to pre-recession peak within 24 months` | Non-tidy (needs custom parser): fred:INDPRO |
| 3 | unemployment_peak_and_recovery | PENDING_DATA |  | `peak unemployment >= 10% AND unemployment(1923) <= 5%` | No usable vintage for: academic:lebergott_1957_unemployment_series |
| 4 | federal_spending_cut_during_recession | PENDING_EVAL |  | `federal_outlays_share_gdp(1922) <= 0.7 * federal_outlays_share_gdp(1920)` | Non-tidy (needs custom parser): fred:FYONGDA188S |
| 5 | fed_did_not_loosen_during_contraction_1920 | PENDING_EVAL |  | `fed_discount_rate average 1920 >= fed_discount_rate average 1919` | Non-tidy (needs custom parser): fred:M13009USM156NNBR |

## Claim

> The 1920-1921 US depression — a sharp post-WW1 contraction featuring industrial production collapse on the order of 30% and unemployment rising above 10% — was followed by a rapid V-shaped recovery within approximately 18 months, despite the Harding administration cutting federal spending by roughly half over 1920-1922 and the Federal Reserve raising rather than lowering policy rates through much of 1920. The Austrian/laissez-faire reading (Rothbard, Grant, Woods) is that this is the canonical case of a recession allowed to clear via liquidation of malinvestment without either fiscal stimulus or monetary accommodation, demonstrating that recovery can proceed rapidly without the Hoover/FDR-style intervention paradigm. Pre- registered claim is that across at least 4 of 5 canonical metrics (GDP, industrial production, unemployment, federal-spending change, policy-rate stance) the 1920-1921 episode meets the "rapid recovery without stimulus" pattern.

## Interpretation

Verdict is **inconclusive (data gaps)** — 2 metric(s) cannot be evaluated because the underlying data source is not yet in the vintages pipeline, and 3 metric(s) have data but a threshold expression the auto-evaluator does not recognise (complex conditions, discrete event counts, cross-country gaps). Close these gaps then re-run.

## Steelman live concerns

See `hypotheses/steelman/austrian_v_recovery_us_1920_no_fiscal_stim_canonical.md` for the strongest opposing arguments. Canonical-case multi-metric evidence is a pattern match, not a causal identification — the result card should be read as 'outcome trajectory matches the predicted pattern to degree X' rather than 'policy P caused the outcome'.

## Provenance

Vintages pinned in `manifest.yaml`. Full per-metric diagnostics in `diagnostics.json`. Machine-readable results in `metric_results.parquet`.
