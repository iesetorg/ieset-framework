# Result card - spain_2021_2023_inflation_unemployment_resilience

**Verdict:** SUPPORTED - 3/3 metrics passed (support >= 2; refute <= 1).

## Claim

Spain absorbed the 2021-2023 inflation shock with improving unemployment and GDP above its pre-COVID level by late 2023.

## Metrics

| Metric | Value | Threshold | Pass | Details |
|---|---:|---|:---:|---|
| inflation_shock_large | 10.800 | peak yoy CPI >8% | yes | peak 10.8% |
| unemployment_improved_through_shock | 1.890 | >1pp fall 2021Q4 to 2023Q3 | yes | 13.65% to 11.76% |
| gdp_above_pre_shock | 10.051 | >5% above 2019Q4 | yes | 102.4 to 112.7 |

## Interpretation

This is a compact predeclared event-window verdict using local cached national-statistics vintages. It is strong for timing and magnitude, but not a full causal structural decomposition.

## Provenance

See `manifest.yaml` for exact vintage files and SHA-256 hashes. Re-run with `replication.py`.
