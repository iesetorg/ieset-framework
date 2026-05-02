# Result card - uk_furlough_2020_unemployment_output_shield

**Verdict:** SUPPORTED - 3/3 metrics passed (support >= 2; refute <= 1).

## Claim

The UK furlough-era labour-market intervention coincided with a huge 2020 output collapse but contained unemployment and allowed output to return near its pre-pandemic level by late 2021.

## Metrics

| Metric | Value | Threshold | Pass | Details |
|---|---:|---|:---:|---|
| output_collapse | 22.105 | >15% fall from 2019Q4 to 2020Q2 | yes | 670587 to 522356 |
| unemployment_contained | 5.300 | peak 2020Q4-2021Q4 below 6.5% | yes | max 5.3% |
| output_recovered_by_2021q4 | 0.759 | within 2% of 2019Q4 | yes | 670587 to 675680 |

## Interpretation

This is a compact predeclared event-window verdict using local cached national-statistics vintages. It is strong for timing and magnitude, but not a full causal structural decomposition.

## Provenance

See `manifest.yaml` for exact vintage files and SHA-256 hashes. Re-run with `replication.py`.
