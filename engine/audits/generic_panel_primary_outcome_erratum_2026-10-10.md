# Generic panel primary-outcome custody audit — 10 October 2026

This review uses the 729-public, 2,362-hypothesis snapshot at `97c0b67d4af999308a476d6e92267faf14815ddc`. It compares each public generic-panel diagnostic with the current and result-commit hypothesis specification and the `scripts/run_panel_fe.py` code present when that diagnostic was committed. Saved run artifacts and frozen specifications were not edited. **Twenty-four old public records (2 featured, 22 calibration) do not measure their named primary outcome and are withheld from public and school credit pending a source-pinned, claim-matched rerun.** All 24 were already public in the earlier 307-public ledger at `b474810e06`; none is part of the recent 357 additional records.

## Historical execution fault

The first-run panel transformer accepted only `level`, `raw`, `log`, `diff`, `first_diff`, `yoy`, and `log_diff`. Most declared growth and multi-year transforms therefore passed through as raw source levels. The later 17 May change broadened `if "log" in kind` ahead of `log_diff`, so `log_diff` and `annual_log_change` became log **levels** rather than differences. Both versions applied the old `log_diff` with a single Series difference across the entire multi-country source, without resetting at country boundaries. The saved generic runner fit only its first available outcome; a secondary outcome in the spec cannot repair a mismatched primary coefficient.

### Saved selected outcomes with a wrong change transform

The following **15** result packets declared a log or annual change but the runner used the source level: `contract_enforcement_fdi_productivity_spillovers`, `corruption_state_allocation_growth_interaction`, `pension_forced_saving_capital_deepening`, `public_spending_composition_growth`, `government_spending_tfp_drag_panel`, `tax_burden_frontier_growth_non_linear`, `capital_account_openness_institutional_threshold`, `firm_entry_rate_long_run_productivity`, `price_signal_distortion_capital_misallocation`, `public_rd_frontier_innovation_complement`, `singapore_state_capacity_market_openness_combo`, `hong_kong_no_industrial_policy_frontier_comparison`, `vietnam_doi_moi_private_sector_growth_share`, `taiwan_sme_competition_vs_state_planning_growth`, and `thailand_middle_income_plateau_state_coordination`.

`regulatory_predictability_frontier_innovation` declared `log_diff`, but the saved pre-May-17 runner differenced the entire source series without country grouping. Its country-boundary values are not annual within-country growth. `industrial_policy_high_governance_success` was run after the 17 May change; its declared `log_diff` was reduced to a log level. These are **2** more affected records.

### Other selected primary outcome mismatches

The following **7** cases have a different, directly observable mismatch:

| Hypothesis | Saved primary outcome versus declaration |
| --- | --- |
| `government_consumption_share_tfp` | PWT `rtfpna` TFP level passed through as `annual_log_growth`. |
| `welfare_architecture_market_openness_nordic` | WDI real GDP per capita level passed through as `annual_log_growth`. |
| `australia_hawke_keating_reform_long_run` | WDI real GDP per capita level passed through as `log_level` at its pre-May-17 run. |
| `africa_ssa_post_covid_recovery_divergence_2020_2024` | WDI real GDP per capita level passed through as `log_level` at its pre-May-17 run. |
| `frontier_income_volatility_state_allocation` | WDI annual GDP-growth rate passed through as a claimed `rolling_sd_10yr` volatility measure. |
| `long_run_consumption_frontier_market_score_1970_2024` | Aggregate PWT consumption was passed through as a claimed real per-capita ratio to the US frontier and ten-year growth measure. |
| `expropriation_risk_investment_horizon` | Aggregate WDI fixed investment as a GDP share was passed through as a claimed short-term investment-horizon share. |

The superficially similar `import_substitution_long_run_export_underperformance` uses a WDI source that is **already annual GDP growth** (`NY.GDP.PCAP.KD.ZG`), and `financial_liberalisation_crisis_risk` uses an already coded banking-crisis indicator; this transform audit does not withhold either. `debt_overhang_private_investment_30yr` declares an annual-log-change secondary outcome, but the saved generic primary fit selected another outcome; it is outside this primary-outcome disposition. Other claim, source, and model-completeness questions still require case-level review.

## Repair boundary

The panel runner now refuses an outcome that is numerically identical to an included control, rather than dropping that frozen control and changing the model. It now computes supported annual and fixed multi-year log differences from exact prior calendar years within each country; unsupported log-change labels fail closed. These changes affect **future** runs only. The 132 verified archived exact-zero generic results remain archived: 131 register WDI real GDP per capita as both logged outcome and logged control against the same Fraser EFW summary-index treatment, while the remaining welfare-state case's different declared transformations previously collapsed to identical values. Their much broader claims still need direct treatment, outcome, and model-specific designs. No past coefficient, verdict, or registration was rewritten to create a graduation.

The public-evidence quarantine records all 24 primary-outcome failures while retaining the historical files for inspection. Regenerated `engine/evidence_tier_audit.json` and `web/public/evidence-tiers.json` now report **705 public of 2,362** (48 featured, 657 calibration) and 1,657 archive. Relative to the old 729 count, 24 pre-existing baseline records lost public credit. The 357 newly added records remain, while the fixed 872-record target is 167 away. A corrected rerun needs a prospective or appropriately frozen claim-matched method, pinned sources, exact replay, and every original sample and falsification gate; a transformer fix alone cannot establish those conditions.
