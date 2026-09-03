# IESET adversarial audit remediation — 2026-09-03

**Remediation ID:** `ieset_adversarial_audit_remediation_2026-09-03`  
**Remediated (UTC):** 2026-09-03T17:44:02Z  
**Source audit:** `engine/audits/ieset_adversarial_supported_claims_2026-07-31.md` (adversarial audit of 20 high-confidence SUPPORTED claims, 2026-07-31, landed verbatim from run `run_ieset_20260731_225132_adversary_kimi_cli`)  
**Remediation gate:** human (this file records dispositions; it is not a silent patch). All corrections are additive — no run content was deleted or overwritten.

## Summary

- Every cross-cutting finding (X1–X7) has an explicit disposition; every audited claim (20/20) has an explicit disposition.
- Detectors A–D are implemented and tested in `scripts/audit_integrity_detectors.py` + `tests/test_audit_integrity_detectors.py` (12 tests, real diagnostics data).
- Detector census: 93 runs with metrics scanned, 36 flagged, 149 findings. 11 of the audited 20 are machine-flagged; 25 additional runs are flagged but unaudited (deferred).
- Verdict-migration ledger (X5): 7 runs recorded.

## Cross-cutting finding dispositions (X1–X7)

| ID | Finding | Disposition | Mechanism |
|---|---|---|---|
| X1 | Unit-mismatched metric evaluation | **fixed_going_forward** | Detector A implemented: scripts/audit_integrity_detectors.py::detect_unit_typetag_mismatch flags absolute-unit thresholds (years, TFR, Gini, millions, pp) evaluated against percent-change stats; covered by tests/test_audit_integrity_detectors.py. Deferred: v2 evaluator must store threshold_unit/stat_unit per metric and hard-fail on mismatch before re-scoring affected runs. |
| X2 | Sentinel ~100 observed values scored MET | **fixed_going_forward** | Detector B implemented: detect_sentinel_values flags percent-family stats >= 99.99 and 1e4-scale values on percent/ratio-family stats. Deferred: Affected METs are marked not-counting in card annotations; verdicts quarantined until the v2 evaluator refuses sentinel stats. |
| X3 | Byte-identical 'independent' sources | **fixed_going_forward** | Detector C implemented: detect_duplicate_source_hash flags metrics whose declared publishers outnumber their distinct vintage files (all-publishers-one-file is the strongest case). Deferred: v2 diagnostics require per-publisher hash attestation; the 'independent data sources' interpretation line is corrected on affected cards. |
| X4 | Sample-scope explosion in panel canonical runs | **fixed_going_forward** | Detector D implemented: detect_sample_explosion + count_exceeds_declared_sample assert countries_meeting_threshold counts never exceed the declared 'of n' sample. Deferred: v2 evaluator must restrict counting to the pre-registered sample list; GFC/Asia runs quarantined until re-scored. |
| X5 | Undocumented verdict migration | **fixed** | Verdict-migration ledger created in this remediation (see verdict_migration_ledger); all seven §E7 runs now carry explicit prior-verdict notes on their cards. Convention adopted: any verdict flip requires an ARCHIVED_v1 directory plus a ledger entry (argentina_institutional_instability_decline/ARCHIVED_v1_false_refuted precedent). |
| X6 | PENDING_EVAL definitional metrics do not gate verdicts | **deferred_with_reason** | Evaluator change (definitional-metric gating at partial) is v2 spec F; not implementable without re-scoring the evaluator, which would silently change verdicts mid-audit. Deferred: Affected cards annotated so the ungated PENDING_EVAL definitional metrics are disclosed on the verdict line; runs quarantined/capped accordingly. |
| X7 | Mechanical / unfalsifiable pcw100 specifications | **rescoped** | pcw100 screens and descriptive growth templates re-labelled to screen_positive / supported (descriptive) tiers via card annotations; quarantined where specifications are mechanically invalid (mw_bite_ratio). Deferred: Scoreboard tier weighting (screens <= 0.25) is a scoreboard regeneration change scheduled with the v2 family. |

## Claim-by-claim dispositions

| # | Run | Disposition | Headline finding |
|---:|---|---|---|
| 1 | `west_east_germany_economic_system_divergence_1950_1989` | **quarantined_pending_v2** | Metric 2 `consumer_goods_availability_wait_time` observed = 100 (1985) — round-number sentinel (X2), not a documented wait-time series. |
| 2 | `north_south_korea_development_divergence_1953_present` | **quarantined_pending_v2** | Metric 6 `famine_episode_count` = 40 (2020) — event-log row count scored as MET; data-glitch signature. |
| 3 | `cuba_socialist_economy_stagnation_1960_2023` | **quarantined_pending_v2** | Metric 3 MET on observed = 100 (1993) sentinel (X2); removing it flips the exactly-at-threshold 7/10 support. |
| 4 | `soviet_union_central_planning_gdp_collapse_1989_1991` | **quarantined_pending_v2** | X2: `gdp_contraction_peak_to_trough` observed 99.99999929185707 (diagnostics.json:28) — physically impossible value scored MET. |
| 5 | `great_leap_forward_famine_output_collapse_1959_1961` | **quarantined_pending_v2** | Metric 10 PENDING_EVAL — the harness could not parse its own pre-registered threshold (X6). |
| 6 | `zimbabwe_hyperinflation_land_reform_output_collapse_2000_2009` | **quarantined_pending_v2** | The definitional Cagan hyperinflation metric is PENDING_EVAL and does not gate the verdict (X6) — a hyperinflation-titled hypothesis supported without it. |
| 7 | `venezuela_chavismo_canonical_case_multi_metric` | **quarantined_pending_v2** | Cagan hyperinflation metric PENDING_EVAL, not gating (X6). |
| 8 | `banking_crisis_2008_gfc_canonical_multimetric` | **quarantined_pending_v2** | X4: 254 entities counted against the pre-registered 'at least 5 of 9 countries' (list includes WLD, EUU, OED aggregates and an empty leading code). |
| 9 | `pcw100_global_efw_trade_freedom_gdp_growth` | **rescoped_screen_positive** | Associational cross-sectional screen (p=0.0015) emitted at full evidentiary weight (X7); reverse causality and state-failure composition of the low quartile unaddressed. |
| 10 | `pcw100_us_mw_bite_ratio_p10_wage` | **quarantined_pending_v2** | Mechanical identity: in high-bite states the p10 wage *is* the minimum wage (R²=0.975) — unfalsifiable as constructed (X7). |
| 11 | `oecd_pdb_gdp_hour_frontier_convergence_1950_2025` | **rescoped_descriptive** | frontier_gap_lag β=3.099 on a lagged level gap — units/normalization red flag (likely 100× misread on the card). |
| 12 | `banking_crisis_japan_1990_lost_decade` | **capped_partial_pending_v2** | The core banking metric `bank_npl_ratio_peak` is PENDING_DATA (no JPN observations 1998-2003); support for a banking-crisis hypothesis rests on zero bank-balance-sheet data. |
| 13 | `vietnam_doi_moi_growth_human_development_1990_2023` | **rescoped_descriptive** | All four thresholds are one-sided trend descriptions most successful developing economies meet — no counterfactual, comparator, or pre-Đổi-Mới baseline; prior ≈ 1.0 undisclosed. |
| 14 | `ethiopia_prewar_growth_human_development_2000_2019` | **rescoped_descriptive** | Post-hoc window ending 2019 excludes the Tigray-war collapse — the strongest contrary observation; break-rule disclosed nowhere. |
| 15 | `banking_crisis_greece_2010_2018_doom_loop` | **quarantined_pending_v2** | X1/X2: unemployment '>=19 pp rise' scored against pct_increase_from_baseline = 1.43e+03; government debt '>=175% of GDP' against max_in_window_fallback = 4.94e+04 — sentinel/wrong-series artefacts scored MET. |
| 16 | `south_korea_growth_health_services_shift_1990_2023` | **rescoped_descriptive** | Template basket with no metric on which schools' predictions diverge (household debt, old-age poverty unmeasured) — support guaranteed ex ante. |
| 17 | `oecd_pdb_post_2008_productivity_hysteresis_panel` | **rescoped_descriptive** | Level-shift dummy with no pre-2008 trend control and no COVID-window handling — documented deceleration misattributed to crisis hysteresis. |
| 18 | `banking_crisis_asian_financial_crisis_1997_panel` | **quarantined_pending_v2** | X4: 62 countries with >=30% depreciation (incl. AUT, BEL, CAN, DEU — no such depreciations occurred) and 167 with >=5% GDP declines, against the pre-registered 'at least 4 of 5 countries'. |
| 19 | `pcw100_global_efw_sound_money_gdp_growth` | **rescoped_screen_positive** | SOM (Somalia) in the top sound-money quartile — index/coding or imputation integrity problem in the input. |
| 20 | `india_growth_health_services_shift_1990_2023` | **rescoped_descriptive** | Per-country threshold drift across the template family (3.5% KOR / 4.0% IND / 5.0% ETH) each set just below the realized value (4.28 / 4.47 / 5.87) — post-hoc calibration signature. |

Full findings per claim are on each run's `result_card.md` (Correction 2026-09-03 section) and in the companion JSON.

## Verdict-migration ledger (X5)

| Run | Prior verdict (§E7) | Undocumented flip to | Disposition now |
|---|---|---|---|
| `west_east_germany_economic_system_divergence_1950_1989` | inconclusive (data gaps, HYPOTHESIS_FRAMEWORK_AUDIT.md §E7) | `supported` | quarantined_pending_v2 |
| `north_south_korea_development_divergence_1953_present` | inconclusive (data gaps, HYPOTHESIS_FRAMEWORK_AUDIT.md §E7) | `supported` | quarantined_pending_v2 |
| `cuba_socialist_economy_stagnation_1960_2023` | inconclusive (data gaps, HYPOTHESIS_FRAMEWORK_AUDIT.md §E7) | `supported` | quarantined_pending_v2 |
| `soviet_union_central_planning_gdp_collapse_1989_1991` | inconclusive (data gaps, HYPOTHESIS_FRAMEWORK_AUDIT.md §E7) | `supported` | quarantined_pending_v2 |
| `great_leap_forward_famine_output_collapse_1959_1961` | inconclusive (data gaps, HYPOTHESIS_FRAMEWORK_AUDIT.md §E7) | `supported` | quarantined_pending_v2 |
| `zimbabwe_hyperinflation_land_reform_output_collapse_2000_2009` | inconclusive (data gaps, HYPOTHESIS_FRAMEWORK_AUDIT.md §E7) | `supported` | quarantined_pending_v2 |
| `venezuela_chavismo_canonical_case_multi_metric` | inconclusive (data gaps, HYPOTHESIS_FRAMEWORK_AUDIT.md §E7) | `supported` | quarantined_pending_v2 |

Convention adopted from this remediation forward: any verdict flip requires an `ARCHIVED_v1_*` directory preserving the prior card plus a ledger entry (precedent: `argentina_institutional_instability_decline/ARCHIVED_v1_false_refuted/`).

## Detector census — flagged but unaudited runs (deferred)

These runs trip the shipped detectors but were not in the audited 20. Disposition: **deferred** — queued for adversarial audit round 2 and the v2 re-score; the list is dominated by the `banking_crisis_*` family the audit predicted shares the sample-explosion harness.

- `abct_fed_funds_below_taylor_rule_capital_misallocation_2002_2007`
- `argentina_paso_2019_fx_reserves_inflation_base_money_lag`
- `banking_crisis_argentina_2001_corralito_canonical`
- `banking_crisis_brazil_1999_real_devaluation`
- `banking_crisis_china_2015_2020_panel`
- `banking_crisis_cyprus_2013_bailin`
- `banking_crisis_iceland_2008_canonical_multimetric`
- `banking_crisis_ireland_2008_property_bust`
- `banking_crisis_italy_2016_2017_mps`
- `banking_crisis_latvia_2008_parex`
- `banking_crisis_lebanon_2019_2024_collapse`
- `banking_crisis_nordic_1991_1993_panel`
- `banking_crisis_russia_1998_default_canonical`
- `banking_crisis_spain_2012_cajas_restructuring`
- `banking_crisis_us_2023_svb_signature`
- `banking_crisis_us_sl_crisis_1986_1995`
- `china_zero_covid_2022_2023_demand_collapse_recovery`
- `cuba_2021_protests_economic_reform_response`
- `fiscal_dominance_japan_debt_non_crisis`
- `mena_lebanon_currency_collapse_real_economy_2019_2024`
- `milei_dollarisation_inflation_collapse_2024_2026`
- `post_covid_labour_reallocation_us_2020_2024`
- `turkey_fx_erdogan_unorthodox_inflation_response_2021_2024`
- `uk_brexit_2016_inflation_real_earnings_window`
- `uk_energy_cpi_real_earnings_squeeze_2022`

## Standing proposals status

- **A_unit_typetag:** implemented as detector; evaluator hard-fail deferred to v2
- **B_sentinel_scan:** implemented as detector
- **C_provenance_diversity:** implemented as detector; per-publisher hash attestation deferred to v2
- **D_sample_restriction:** implemented as detector assertion; evaluator restriction deferred to v2
- **E_verdict_migration_ledger:** implemented (this file)
- **F_definitional_gating:** deferred to v2 evaluator (X6)
- **v2_evidentiary_tiers:** card annotations applied; scoreboard weighting deferred to v2

## What re-activates these verdicts

A v2 re-score with: unit typetags stored and hard-failed on mismatch; sentinel stats refused; per-publisher hash attestation; counting restricted to pre-registered samples; definitional metrics gating at `partial`; screens emitting tiered verdicts. Until then the affected cards render their quarantine/re-scope banners and the public correction in `DISCLOSURE.md` stands.

