# Result card — anglo_money_growth_public_crowding_stagnation_2019_2024

**Verdict:** INCONCLUSIVE_DATA_PENDING

**Reason:** 1 joint pattern(s) MET, 1 PENDING (broad money coverage gap); support threshold of 3 cannot be reached either way

Pre-registered rule: SUPPORT if >= 5 of 6 metrics met; REFUTED if >= 1 confirmed NOT_MET with no path to support; otherwise INCONCLUSIVE_DATA_PENDING.

**Counts:** 3 MET · 2 NOT_MET · 1 PENDING_DATA · 0 PENDING_EVAL

**Primary country:** GBR

## Metric-by-metric

| # | Metric | Status | Observed | Threshold | Notes |
|---|---|:---:|---:|---|---|
| 1 | gbr_money_stagnation_pattern | MET | 28.79 [cumulative_broad_money_growth_pct] | `cumulative money growth >= 20% AND per-capita growth <= USA-2pp AND private consumption growth < USA` | money 28.8%, pc 0.9%, priv -0.8%, gov-share change 1.3pp (to 2023); USA pc 11.5%, priv 10.5% |
| 2 | can_money_stagnation_pattern | PENDING_DATA | — | `cumulative money growth >= 20% AND per-capita growth <= USA-2pp AND private consumption growth < USA` | broad money growth series has no observations in the window for this unit (WDI coverage gap); the joint pattern cannot be evaluated |
| 3 | aus_money_stagnation_pattern | NOT_MET | 65.24 [cumulative_broad_money_growth_pct] | `cumulative money growth >= 20% AND per-capita growth <= USA-2pp AND private consumption growth < USA` | money 65.2%, pc 4.6%, priv 11.3%, gov-share change 1.9pp (to 2024); USA pc 11.5%, priv 10.5% |
| 4 | nzl_money_stagnation_pattern | NOT_MET | 38.11 [cumulative_broad_money_growth_pct] | `cumulative money growth >= 20% AND per-capita growth <= USA-2pp AND private consumption growth < USA` | money 38.1%, pc 5.0%, priv 11.6%, gov-share change 2.0pp (to 2022); USA pc 11.5%, priv 10.5% |
| 5 | public_share_stays_elevated | MET | 3.00 [countries_with_gov_share_up_1pp] | `at least 3 of 4 welfare-Anglo countries keep gov consumption share >= 1pp above 2019` | 3 of 4 welfare-Anglo units hold the public-consumption share >= 1pp above 2019 |
| 6 | usa_contrast_leg | MET | 11.47 [usa_cumulative_pc_growth_pct] | `USA shows comparable money growth with per-capita growth above every welfare-Anglo unit` | USA money 57.9%, pc 11.5% |

## Claim

> Across the welfare-state Anglo economies (United Kingdom, Canada, Australia, New Zealand) in 2019-2024, broad money expansion of 20 percent or more cumulatively coincides with real stagnation rather than real growth: countries with money growth in the top of the distribution show lower cumulative GDP-per-capita growth, lower cumulative private consumption growth, and government consumption shares at least one point above their pre-2019 level, while the United States — with comparable money growth — shows the private-consumption and per-capita recovery the welfare-Anglo set lacks. At least three of the four welfare-Anglo countries display the money-growth-without-private-recovery pattern.

## Interpretation

Metrics evaluated against the pre-registered thresholds on the named derived panels; PENDING_* metrics disclose exactly which source is missing and are not counted toward support. This card is produced by scripts/run_derived_panel_checklist.py from the pinned panel vintages recorded per metric.

## Provenance

- spec: hypotheses/monetary/anglo_money_growth_public_crowding_stagnation_2019_2024.yaml
- runner: scripts/run_derived_panel_checklist.py
- run_utc: 2026-09-03T20:16:43.428907Z
- gbr_money_stagnation_pattern: data/derived/anglo_public_private_stagnation_panel.parquet sha256=4c51f5068a0f70bd…
- aus_money_stagnation_pattern: data/derived/anglo_public_private_stagnation_panel.parquet sha256=4c51f5068a0f70bd…
- nzl_money_stagnation_pattern: data/derived/anglo_public_private_stagnation_panel.parquet sha256=4c51f5068a0f70bd…
- public_share_stays_elevated: data/derived/anglo_public_private_stagnation_panel.parquet sha256=4c51f5068a0f70bd…
- usa_contrast_leg: data/derived/anglo_public_private_stagnation_panel.parquet sha256=4c51f5068a0f70bd…
