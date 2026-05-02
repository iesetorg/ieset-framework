# Result card - uk_brexit_2016_inflation_real_earnings_window

**Verdict:** SUPPORTED - 3/3 metrics passed (support >= 2; refute <= 1).

## Claim

The 2016 Brexit referendum shock produced a clear near-term UK inflation pass-through and a squeeze in CPI-deflated weekly earnings over the 2016Q2-2017Q4 event window.

## Metrics

| Metric | Value | Threshold | Pass | Details |
|---|---:|---|:---:|---|
| cpih_inflation_step_up | 1.600 | >1pp 2016 to 2017 | yes | 1.0% to 2.6% |
| cpi_level_pass_through | 4.183 | >3.5% cumulative CPI increase | yes | 100.4 to 104.6 |
| real_weekly_earnings_squeeze | -0.906 | <0% real weekly earnings growth | yes | KAB9/CPI 4.920 to 4.876 |

## Interpretation

This is a compact predeclared event-window verdict using local cached national-statistics vintages. It is strong for timing and magnitude, but not a full causal structural decomposition.

## Provenance

See `manifest.yaml` for exact vintage files and SHA-256 hashes. Re-run with `replication.py`.
