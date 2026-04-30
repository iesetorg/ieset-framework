# Result card — austrian_kirzner_entrepreneurship_business_dynamism_decline_us_1980_2020

**Verdict:** inconclusive (data gaps)

**Reason:** 0 metrics met, 5 pending; 4 more need resolution

Pre-registered rule: SUPPORT if >= 4 of 5 metrics met; REFUTE if <= 2 met (impossible to hit support).

**Counts:** 0 MET · 0 NOT_MET · 5 PENDING_DATA · 0 PENDING_EVAL

**Primary country:** USA

## Metric-by-metric

| # | Metric | Status | Observed | Threshold | Notes |
|---|---|:---:|---:|---|---|
| 1 | firm_formation_rate_decline | PENDING_DATA |  | `>= 25% decline 1980-2018` | No usable vintage for: bls:business_dynamics_statistics_firm_births |
| 2 | young_firm_employment_share_decline | PENDING_DATA |  | `>= 30% decline 1980-2018` | No usable vintage for: bls:business_dynamics_statistics_young_firm_employment |
| 3 | job_reallocation_rate_decline | PENDING_DATA |  | `>= 20% decline 1980-2018` | No usable vintage for: bls:business_dynamics_statistics_job_reallocation |
| 4 | occupational_licensing_growth | PENDING_DATA |  | `>= 2x growth in licensed-share 1970-2010` | No usable vintage for: academic:kleiner_krueger_occupational_licensing |
| 5 | industry_concentration_rise | PENDING_DATA |  | `>= 60% of NAICS sectors show top-4 share rising 1980-2017` | No usable vintage for: us_census:economic_census_concentration_ratios |

## Claim

> US business-dynamism measures — the firm-formation rate (new establishments per 1000 working-age population), the job- reallocation rate, and the share of employment in firms aged 0-5 — declined materially over 1980-2020. Across US states, the magnitude of the dynamism decline is positively associated with the cumulative growth of state-level occupational-licensing prevalence, federal-regulation cost burden allocated to the state, and industry-concentration indices. The Kirznerian-Austrian prediction is that entrepreneurship is a discovery process whose rate of operation depends on the openness of entry, and that rising regulatory and concentration barriers progressively suppress it. Pre-registered claim is that across 4 of 5 canonical metrics (firm formation rate, share of young-firm employment, job reallocation rate, occupational-licensing prevalence, industry concentration), the post-1980 trajectory shows statistically and economically significant deterioration.

## Interpretation

Verdict is **inconclusive (data gaps)** — 5 metric(s) cannot be evaluated because the underlying data source is not yet in the vintages pipeline, and 0 metric(s) have data but a threshold expression the auto-evaluator does not recognise (complex conditions, discrete event counts, cross-country gaps). Close these gaps then re-run.

## Steelman live concerns

See `hypotheses/steelman/austrian_kirzner_entrepreneurship_business_dynamism_decline_us_1980_2020.md` for the strongest opposing arguments. Canonical-case multi-metric evidence is a pattern match, not a causal identification — the result card should be read as 'outcome trajectory matches the predicted pattern to degree X' rather than 'policy P caused the outcome'.

## Provenance

Vintages pinned in `manifest.yaml`. Full per-metric diagnostics in `diagnostics.json`. Machine-readable results in `metric_results.parquet`.
