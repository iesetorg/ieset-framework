# Result card — argentina_milei_disinflation_monetary_reconfiguration_2023_2028

**Verdict:** SUPPORTED

**Reason:** 4 of 6 metrics met threshold (support threshold 4)

Pre-registered rule: SUPPORT if >= 4 of 6 metrics met; REFUTED if >= 2 confirmed NOT_MET with no path to support; otherwise INCONCLUSIVE_DATA_PENDING.

**Counts:** 4 MET · 2 NOT_MET · 0 PENDING_DATA · 0 PENDING_EVAL

**Primary country:** ARG

## Metric-by-metric

| # | Metric | Status | Observed | Threshold | Notes |
|---|---|:---:|---:|---|---|
| 1 | disinflation_half_from_peak | MET | 289.40 [cpi_yoy_peak_pct] | `cpi_yoy_pct <= 0.5 x max(cpi_yoy_pct over 2023-10..2024-04) for every observed month of 2026` | 2023-10..2024-04 peak y/y=289.4%; every observed 2026 month <= 144.7% (n=7 observed months) |
| 2 | monthly_cpi_stabilised | MET | 16.00 [months_below_3pct_mom] | `at least 12 of the last 18 observed months have cpi_mom_pct < 3.0` | 16 of last 18 observed months below 3.0% m/m |
| 3 | monetary_base_growth_collapse | NOT_MET | 5.00 [consecutive_months_below_30pct] | `monetary_base_yoy_pct < 30 for 12 consecutive observed months by 2026-12` | current trailing streak 5 months below 30% (latest 7.2% at 2026-08-01) |
| 4 | private_money_normalisation | NOT_MET | 10.00 [consecutive_months_below_40pct] | `m2_private_yoy_pct < 40 for 12 consecutive observed months by 2026-12` | current trailing streak 10 months below 40% |
| 5 | fx_gap_closure | MET | 2.49 [median_fx_gap_pct] | `median fx_gap_pct < 10.0 over observed 2025 months` | median retail/wholesale gap over 12 observed 2025 months / spec upstream: bcra:4; bcra:5 |
| 6 | reserves_rebuilt | MET | 2.24 [reserve_ratio_to_trough] | `reserves_usd >= 1.25 x min(reserves_usd over 2023-10..2024-02) by 2026-12` | latest reserves 48259 vs trough 21513 (ratio 2.24) |

## Claim

> Argentina's December 2023 stabilization turn (fiscal anchor, monetary base discipline, cepo relaxation under the Milei government) produces a durable monetary reconfiguration rather than a repeat of past disinflation reversals: consumer inflation falls by at least half from its late-2023 peak, monthly inflation stabilizes below 3 percent, monetary base and private M2 growth collapse to below 30 percent year-over-year, the retail-wholesale FX gap closes below 10 percent, and international reserves rebuild by at least 25 percent — with at least four of the six metrics met by end-2026 and none of the reversal markers firing.

## Interpretation

Metrics evaluated against the pre-registered thresholds on the named derived panels; PENDING_* metrics disclose exactly which source is missing and are not counted toward support. This card is produced by scripts/run_derived_panel_checklist.py from the pinned panel vintages recorded per metric.

## Provenance

- spec: hypotheses/monetary/argentina_milei_disinflation_monetary_reconfiguration_2023_2028.yaml
- runner: scripts/run_derived_panel_checklist.py
- run_utc: 2026-09-03T20:16:42.442069Z
- disinflation_half_from_peak: data/derived/argentina_milei_stabilisation_panel.parquet sha256=cbe8c831b498d38a…
- monthly_cpi_stabilised: data/derived/argentina_milei_stabilisation_panel.parquet sha256=cbe8c831b498d38a…
- monetary_base_growth_collapse: data/derived/argentina_milei_stabilisation_panel.parquet sha256=cbe8c831b498d38a…
- private_money_normalisation: data/derived/argentina_milei_stabilisation_panel.parquet sha256=cbe8c831b498d38a…
- fx_gap_closure: data/derived/argentina_milei_stabilisation_panel.parquet sha256=cbe8c831b498d38a…
- reserves_rebuilt: data/derived/argentina_milei_stabilisation_panel.parquet sha256=cbe8c831b498d38a…
