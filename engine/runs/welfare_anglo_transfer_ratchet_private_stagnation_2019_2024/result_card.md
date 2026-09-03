# Result card — welfare_anglo_transfer_ratchet_private_stagnation_2019_2024

**Verdict:** REFUTED

**Reason:** 2 welfare-Anglo unit(s) gave back > 1pp and/or the USA contrast failed

Pre-registered rule: SUPPORT if >= 5 of 6 metrics met; REFUTED if >= 1 confirmed NOT_MET with no path to support; otherwise INCONCLUSIVE_DATA_PENDING.

**Counts:** 3 MET · 3 NOT_MET · 0 PENDING_DATA · 0 PENDING_EVAL

**Primary country:** GBR

## Metric-by-metric

| # | Metric | Status | Observed | Threshold | Notes |
|---|---|:---:|---:|---|---|
| 1 | gbr_ratchet | NOT_MET | 2.14 [gov_share_giveback_pp] | `peak-to-latest give-back <= 1.0 percentage point on gov consumption share` | peak 22.4% -> latest 20.2% (2023) |
| 2 | can_ratchet | NOT_MET | 1.80 [gov_share_giveback_pp] | `peak-to-latest give-back <= 1.0 percentage point on gov consumption share` | peak 22.7% -> latest 20.9% (2023) |
| 3 | aus_ratchet | MET | 0.22 [gov_share_giveback_pp] | `peak-to-latest give-back <= 1.0 percentage point on gov consumption share` | peak 22.4% -> latest 22.1% (2024) |
| 4 | nzl_ratchet | MET | 0.20 [gov_share_giveback_pp] | `peak-to-latest give-back <= 1.0 percentage point on gov consumption share` | peak 21.1% -> latest 20.9% (2022) |
| 5 | usa_contrast_giveback | MET | 1.15 [gov_share_giveback_pp] | `USA give-back > 1.0 percentage point from its post-2019 peak` | USA peak-to-latest give-back 1.1pp (2022 latest observed) |
| 6 | ratchet_pattern_count | NOT_MET | 2.00 [countries_without_giveback] | `at least 3 of 4 welfare-Anglo countries with give-back <= 1.0pp` | 2 of 4 welfare-Anglo units hold their post-2019 peak within 1pp |

## Claim

> In the welfare-state Anglo economies (GBR, CAN, AUS, NZL), the government consumption and expense shares ratchet upward through the 2019-2024 stagnation — the post-2019 peak in the public-spending share is never given back by more than one percentage point by 2024 — while private consumption and per-capita growth stagnate, and at least one of the four experiences a bond-market stress event (the UK's September 2022 gilt/LDI episode) without subsequent transfer retrenchment. The claim is that the transfer-public spending level is politically irreversible downward even under stagnation and bond stress, in contrast to the USA where the public-consumption share falls back toward its pre-2019 level.

## Interpretation

Metrics evaluated against the pre-registered thresholds on the named derived panels; PENDING_* metrics disclose exactly which source is missing and are not counted toward support. This card is produced by scripts/run_derived_panel_checklist.py from the pinned panel vintages recorded per metric.

## Provenance

- spec: hypotheses/welfare_architecture/welfare_anglo_transfer_ratchet_private_stagnation_2019_2024.yaml
- runner: scripts/run_derived_panel_checklist.py
- run_utc: 2026-09-03T20:16:43.940571Z
- gbr_ratchet: data/derived/anglo_public_private_stagnation_panel.parquet sha256=4c51f5068a0f70bd…
- can_ratchet: data/derived/anglo_public_private_stagnation_panel.parquet sha256=4c51f5068a0f70bd…
- aus_ratchet: data/derived/anglo_public_private_stagnation_panel.parquet sha256=4c51f5068a0f70bd…
- nzl_ratchet: data/derived/anglo_public_private_stagnation_panel.parquet sha256=4c51f5068a0f70bd…
- usa_contrast_giveback: data/derived/anglo_public_private_stagnation_panel.parquet sha256=4c51f5068a0f70bd…
- ratchet_pattern_count: data/derived/anglo_public_private_stagnation_panel.parquet sha256=4c51f5068a0f70bd…
