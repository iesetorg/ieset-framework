# Result card - uk_erm_exit_1992_output_unemployment_inflation

**Verdict:** SUPPORTED - 3/3 metrics passed (support >= 2; refute <= 1).

## Claim

The UK's September 1992 ERM exit was followed by a rapid real-output rebound and disinflation, while unemployment lagged the recovery rather than improving immediately.

## Metrics

| Metric | Value | Threshold | Pass | Details |
|---|---:|---|:---:|---|
| real_gdp_rebound_four_quarters | 3.366 | >2% increase | yes | 374537 to 387143 |
| unemployment_lagged_peak | 0.700 | >0.5pp rise by 1993Q1 | yes | 9.9% to 10.6% |
| inflation_deceleration | 1.800 | >1pp fall by 1993Q4 | yes | 4.0% to 2.2% |

## Interpretation

This is a compact predeclared event-window verdict using local cached national-statistics vintages. It is strong for timing and magnitude, but not a full causal structural decomposition.

## Provenance

See `manifest.yaml` for exact vintage files and SHA-256 hashes. Re-run with `replication.py`.
