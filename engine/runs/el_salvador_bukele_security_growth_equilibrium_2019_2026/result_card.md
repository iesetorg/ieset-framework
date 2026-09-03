# Result card — el_salvador_bukele_security_growth_equilibrium_2019_2026

**Verdict:** SUPPORTED

**Reason:** 4 of 6 metrics met threshold (support threshold 4)

Pre-registered rule: SUPPORT if >= 4 of 6 metrics met; REFUTED if >= 2 confirmed NOT_MET with no path to support; otherwise INCONCLUSIVE_DATA_PENDING.

**Counts:** 4 MET · 2 NOT_MET · 0 PENDING_DATA · 0 PENDING_EVAL

**Primary country:** SLV

## Metric-by-metric

| # | Metric | Status | Observed | Threshold | Notes |
|---|---|:---:|---:|---|---|
| 1 | homicide_collapse_durable | MET | 7.90 [max_homicide_rate_per_100k] | `homicide_rate_per_100k < 10 in 2022 and every later observed year` | observed through 2022 (WDI vintage coverage); pre-era peak 107.6 |
| 2 | growth_matches_peers | NOT_MET | -0.15 [growth_premium_vs_peer_mean_pp] | `mean gdp_real_growth_pct (2019-2024) >= peer mean over same years` | SLV 2.59% vs peer mean 2.74% (8 pinned peers) |
| 3 | fdi_recovers | MET | 0.46 [fdi_era_minus_pre_pp] | `mean fdi_net_inflows_pct_gdp (2019-2024) >= mean (2010-2018)` | era 1.92% vs pre-era 1.45% of GDP |
| 4 | credit_depth_holds | MET | 8.89 [credit_era_minus_pre_pp] | `mean credit_to_private_pct_gdp (2019-2024) >= mean (2010-2018) minus 5 percentage points` | era 62.1% vs pre-era 53.2% of GDP |
| 5 | remittance_dependence_not_worsening | NOT_MET | 5.22 [remittance_era_minus_pre_pp] | `mean remittances_pct_gdp (2019-2024) <= mean (2010-2018) + 5 percentage points` | era 24.0% vs pre-era 18.8% of GDP |
| 6 | pc_growth_nonnegative | MET | 2.27 [mean_gdp_pc_growth_pct] | `mean gdp_pc_real_growth_pct (2019-2024) >= 0` | mean per-capita growth 2019-2024 2.27% |

## Claim

> El Salvador's post-2019 security-state equilibrium (mass incarceration campaign and gang crackdown from the March 2022 state of exception) produced a durable growth-security equilibrium rather than a repression tax on the economy: homicides collapse below 10 per 100,000 and stay there, real GDP growth matches or beats the Latin American peer mean, FDI recovers above its 2010-2018 mean, credit depth holds within five points of its pre-era level, remittance dependence does not worsen, and GDP-per-capita growth is nonnegative — at least four of six metrics met through 2024, with none of the reversal markers firing.

## Interpretation

Metrics evaluated against the pre-registered thresholds on the named derived panels; PENDING_* metrics disclose exactly which source is missing and are not counted toward support. This card is produced by scripts/run_derived_panel_checklist.py from the pinned panel vintages recorded per metric.

## Provenance

- spec: hypotheses/institutional_quality/el_salvador_bukele_security_growth_equilibrium_2019_2026.yaml
- runner: scripts/run_derived_panel_checklist.py
- run_utc: 2026-09-03T20:16:42.937101Z
- homicide_collapse_durable: data/derived/el_salvador_bukele_growth_panel.parquet sha256=ce2cec282fa8c91f…
- growth_matches_peers: data/derived/el_salvador_bukele_growth_panel.parquet sha256=ce2cec282fa8c91f…
- fdi_recovers: data/derived/el_salvador_bukele_growth_panel.parquet sha256=ce2cec282fa8c91f…
- credit_depth_holds: data/derived/el_salvador_bukele_growth_panel.parquet sha256=ce2cec282fa8c91f…
- remittance_dependence_not_worsening: data/derived/el_salvador_bukele_growth_panel.parquet sha256=ce2cec282fa8c91f…
- pc_growth_nonnegative: data/derived/el_salvador_bukele_growth_panel.parquet sha256=ce2cec282fa8c91f…
