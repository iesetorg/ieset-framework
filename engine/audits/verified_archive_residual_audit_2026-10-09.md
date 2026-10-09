# Verified archive residual audit — 2026-10-09

This is a read-only review of the live source specs, runs, and public evidence gate. It does not assign a verdict or grant scoreboard credit. The full ID list and simultaneous exclusion reasons are in `engine/audits/hypothesis_conversion_funnel_2026-10-09.json`.

## Finding

**No additional verified archived hypothesis has a complete, honest conversion under its current frozen specification and the local corpus.** This is a current-evidence finding, not a claim that a later exact rerun with newly available declared data can never succeed.

The live conversion-funnel `--check` passed: 1,930 hypotheses, 396 public visible, 214 verified archived. The 214 split into 155 estimator repair/rerun, 45 data or design rerun, 3 integrity reconcile/rerun, 8 missing result rerun, 2 prospective rule version, and 1 replication path review. These are first-action buckets, not disjoint reasons. Across the 214, the public gate finds 155 estimator-floor failures, 46 non-result verdicts, 31 missing replication paths, 9 missing canonical verdicts, 4 unsharpened rules, and 3 audit quarantines. Each of the 214 has at least one current exclusion.

## Apparent quick conversions reviewed

| ID(s) | Current evidence boundary |
| --- | --- |
| `tariff_protection_duration_growth_drag` | `replication.py` and manifest are absent. The old generic result estimates a tariff-level main effect, while the frozen rule requires **constructed protection duration** and both export and consumption outcomes. Its diagnostic data status lacks protection duration and export complexity. The old `PARTIAL` label does not establish the registered test. |
| `bis_corporate_credit_boom_investment_slowdown_panel_1970_2025`, `bis_corporate_dsr_investment_slowdown_panel_1999_2025`, `bis_credit_gap_private_investment_reversal_panel`, `bis_credit_gap_private_investment_slowdown_panel_1970_2025`, `bis_reer_volatility_investment_drag_panel_1964_2026` | The only explicit stored labels are `INCONCLUSIVE_DATA_PENDING`. All five fall below their registered minimum country count (14 or 2 observed versus 20 or 15 required). A coefficient or p-value cannot replace the coverage gate. |
| `oecd_pdb_market_reform_productivity_compounder`, `oecd_pdb_public_sector_share_productivity_drag`, `oecd_pdb_tfp_growth_frontier_persistence_1970_2025` | Diagnostics store `REFUTED_OR_WEAK` as `status`, with no canonical verdict. The frozen rule distinguishes support from an unspecified “partial or weak” remainder. These local first-pass throughput screens cannot be relabeled as a determinate refutation from the result-card prose. |
| `oecd_epl_growth_shock_unemployment_persistence_panel` | Quarantined; its required raw contrast is undefined, so the earlier `REFUTED` label misgraded an unmeasurable gate. |
| `oecd_pdb_hours_reduction_output_tradeoff_panel` | Quarantined; its frozen sign rule tests the opposite direction from the English no-output-loss claim. |
| `pcw100_us_mw_bite_ratio_p10_wage` | Quarantined; the observed relationship is largely a mechanical identity. |

Two multi-metric cases deserve a separate schema review. `argentina_milei_disinflation_monetary_reconfiguration_2023_2028` and `el_salvador_bukele_security_growth_equilibrium_2019_2026` were registered before their runs and have explicit `canonical_metrics` and `multi_metric_falsification`, but no `falsification.rule`; the public ledger therefore marks `falsification_rule_unsharpened`. Merely accepting those alternate fields would not justify conversion. Argentina's run declared `SUPPORTED` using observations only through July 2026 for an end-2026 durability claim; the remaining months can change the result, and the claim's reversal markers have no separately declared test. El Salvador's run marked homicide durability `MET` using 2022 as the last observed homicide year, while its claim and metric window extend through 2024; local 2023–24 homicide cells are null. Both need a fully specified, temporally complete decision before public credit. An ex-post reversal-marker definition would require prospective versioning.

## Why the generic preflight is insufficient

The read-only inconclusive preflight returned six `preflight_ready` IDs. Two have **unverified registration** and are outside the 214: `redistribution_tax_transfer_mobility_oecd` and `zimbabwe_land_reform_cause_decomposition`. The four verified IDs do not clear their full registered tests:

| Verified ID | Full-rule blocker despite generic preflight |
| --- | --- |
| `latam_extra_fiscal_rule_adoption_panel_1999_2024` | The frozen group-time replay lacks the registered pre-adoption primary outcome for Brazil and Peru. Its claim names Mexico as an adopter while the registered treatment source omits Mexico. |
| `high_income_escape_market_openness_1950_2024` | Generic preflight sees the first loaded outcome and treatment, but the frozen test requires their interaction with domestic competition. The stored run had four complete-case observations and no loaded human-capital control. |
| `privatisation_transition_tfp_panel` | The frozen exact replay finds zero countries with within-country mass-privatisation treatment changes after the registered WGI control begins; country fixed effects absorb the treatment. |
| `czech_slovak_market_transition_comparison` | The frozen two-spec design requires 1993 and 2024 endpoints for all three decomposition channels. None of its 11 declared countries has both complete endpoints. |

The generic preflight checks an initial loadable estimand; it cannot certify multi-outcome, multi-channel, interaction, group-time, or endpoint conditions. Its six apparent candidates therefore yield **zero** verified archive conversions.

## Estimator queue cross-check

The 155 estimator-blocked records include 135 `effectively_zero`, 22 `primary_estimator_failed`, and 8 `rank_deficiency` findings, with overlap. Twenty primary failures appear in result-card text rather than the top-level diagnostic fields scanned by `audit_evidence_tiers.py`; the same fallback failure is also present in `diagnostics.estimate.method`. Eight of those have decisive-looking `SUPPORTED` or `REFUTED` labels, but they came from statsmodels fixed-effects fallbacks after the primary linearmodels estimator failed: `caribbean_climate_resilience_panel_1990_2024`, `costa_rica_social_democratic_model_1980_2024`, `dominican_tourism_freezone_model_1980_2024`, `japan_miti_success_then_stagnation_panel`, `judicial_independence_growth_persistence`, `korea_post_chaebol_liberalisation_frontier_growth`, `peru_post_fujimori_growth_2001_2019`, and `uruguay_frente_amplio_social_investment_2005_2020`. Removing a warning or copying a label is not an estimator repair. A future exact rerun must clear the frozen model and all declared outcome and robustness conditions.

## Verification scope

- `venv/bin/python scripts/report_hypothesis_conversion_funnel.py --as-of 2026-10-09 --check` passed and reported `396 visible / 1930 hypotheses; 214 verified archived`.
- `venv/bin/python scripts/rerun_preflight_ready_inconclusive.py` was run without `--apply`; it reported 98 blocked, 43 unknown template, 7 missing spec variables, 6 initially ready, and 3 stub rule. It did not change run artifacts.
- The targeted cases above were compared with their current YAML, diagnostics, result cards, replication paths, frozen source-lock runners where present, and local derived panels. No status, verdict, run, or source spec was changed for this audit.
