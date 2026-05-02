# Result card - spain_covid_2020_gdp_unemployment_shock

**Verdict:** SUPPORTED - 3/3 metrics passed (support >= 2; refute <= 1).

## Claim

Spain's 2020 COVID lockdown generated a severe GDP shock and a meaningful unemployment rise, but the unemployment-rate increase was much smaller than the output collapse implied.

## Metrics

| Metric | Value | Threshold | Pass | Details |
|---|---:|---|:---:|---|
| gdp_lockdown_contraction | 21.949 | >15% yoy fall in 2020Q1 | yes | 112.2 to 87.6 |
| unemployment_elevated | 15.980 | 2020Q4 unemployment >15% | yes | 15.98% |
| employment_proxy_not_total_collapse | 15.980 | 2020Q4 unemployment <20% | yes | 15.98% |

## Interpretation

This is a compact predeclared event-window verdict using local cached national-statistics vintages. It is strong for timing and magnitude, but not a full causal structural decomposition.

## Provenance

See `manifest.yaml` for exact vintage files and SHA-256 hashes. Re-run with `replication.py`.
