# Result card - uk_energy_cpi_real_earnings_squeeze_2022

**Verdict:** SUPPORTED - 3/3 metrics passed (support >= 2; refute <= 1).

## Claim

The 2022 UK energy-price shock produced high CPIH inflation and a material CPI-deflated weekly-earnings squeeze.

## Metrics

| Metric | Value | Threshold | Pass | Details |
|---|---:|---|:---:|---|
| inflation_spike_2022 | 7.900 | 2022 CPIH inflation >6% | yes | 7.9% |
| inflation_persistence_2023 | 6.800 | 2023 CPIH inflation >5% | yes | 6.8% |
| real_weekly_earnings_squeeze | -4.093 | <-2% real weekly earnings growth | yes | KAB9/CPI 5.201 to 4.988 |

## Interpretation

This is a compact predeclared event-window verdict using local cached national-statistics vintages. It is strong for timing and magnitude, but not a full causal structural decomposition.

## Provenance

See `manifest.yaml` for exact vintage files and SHA-256 hashes. Re-run with `replication.py`.
