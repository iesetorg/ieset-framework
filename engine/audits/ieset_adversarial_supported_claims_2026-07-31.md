<!--
Verbatim copy of the adversarial audit deliverable produced by the_adversary
(kimi_cli) in run run_ieset_20260731_225132_adversary_kimi_cli (2026-07-31),
landed into engine/audits/ by the human gate on 2026-09-03 as part of
remediation ieset_adversarial_audit_remediation_2026-09-03.
No content edits; fence indentation removed only.
-->
# IESET adversarial audit — 20 high-confidence supported claims
**Audit ID:** ieset_20260731_adversary_audit_20_supported_claims
**Date:** 2026-07-31
**Auditor role:** the_adversary (adversarial_framework_review lane) — reviews and attacks only; no implementation.
**Corpus selection rule:** all `engine/runs/*/result_card.md` with verdict `supported`/`SUPPORTED` were enumerated (100+ runs); 20 were selected to span (a) the canonical-case multi-metric family, (b) the pcw100 associational-screen family, (c) the growth-health-services template family, (d) OECD PDB panel regressions. Selection deliberately includes the seven runs that `HYPOTHESIS_FRAMEWORK_AUDIT.md` §E7 listed as `inconclusive (data gaps)` and that have since migrated to `supported`.

---

## Cross-cutting findings (apply to multiple claims; cited per-claim below)

- **X1. Unit-mismatched metric evaluation.** The canonical-case engine computes a stat (e.g. `peak_to_trough_pct_decline`, `pct_increase_from_baseline`) and compares it numerically against thresholds expressed in different units (years, percentage points, absolute TFR, counts). Percent declines of 11.6 are accepted as ">5 year decline"; 98.2 as ">0.5 TFR decline"; 1.43e+03 as ">=19 pp rise". This mechanically manufactures METs (and one absurd NOT_MET) across the canonical family.
- **X2. Sentinel ~100 observed values.** Multiple cards show observed = 100 (or 99.999999…) for `peak_to_trough_pct_decline` where the true value is ~25–45% (e.g. Soviet real GDP contraction observed_value = 99.99999929185707 in `engine/runs/soviet_union_central_planning_gdp_collapse_1989_1991/diagnostics.json:28`). A 100% decline is physically impossible for a continuing economy; this is a fallback/sentinel being scored as MET.
- **X3. "Independent sources" are byte-identical files.** In `engine/runs/soviet_union_central_planning_gdp_collapse_1989_1991/diagnostics.json`, `rosstat:demographic_yearbook` and `human_mortality_database:RUS` share sha256 `da0c27…`; `oecd:sopemi`, `israel_cbs:immigration_statistics`, and `destatis_germany:aussiedler_statistics` all share sha256 `84822c…`. Three-to-four supposedly independent publishers are the same bytes. The boilerplate interpretation line in every canonical card ("each metric is drawn from an independent data source… probability of pipeline fault across all sources simultaneously is low") is therefore unsubstantiated as written.
- **X4. Sample-scope explosion in panel canonical runs.** Pre-registered "at least k of n named countries" tests were evaluated against the entire world panel including region aggregates. `banking_crisis_2008_gfc_canonical_multimetric/result_card.md` metric 1 reports "254 countries meet >=4" (list includes WLD, EUU, OED, AFE, and an empty leading entry) against a rule requiring 5 of 9 named advanced economies. `banking_crisis_asian_financial_crisis_1997_panel` reports 167 countries with ≥5% real-GDP declines in 1997–1999 — a count that includes China, India, and the World aggregate and is not credible as a peak-to-trough recession count.
- **X5. Undocumented verdict migration.** §E7 of `HYPOTHESIS_FRAMEWORK_AUDIT.md` lists `cuba_socialist_economy_stagnation_1960_2023`, `great_leap_forward_famine_output_collapse_1959_1961`, `north_south_korea_development_divergence_1953_present`, `soviet_union_central_planning_gdp_collapse_1989_1991`, `venezuela_chavismo_canonical_case_multi_metric`, `west_east_germany_economic_system_divergence_1950_1989`, `zimbabwe_hyperinflation_land_reform_output_collapse_2000_2009` as inconclusive on data gaps pending fetchers (`maddison_project`, `bank_of_korea_dprk_estimates`, `imf_weo_historical`). All seven now read `supported`. No migration ledger, changelog, or archived prior verdict accompanies the flip (contrast `argentina_institutional_instability_decline/ARCHIVED_v1_false_refuted/`, which does archive).
- **X6. Definitional metrics PENDING_EVAL do not gate verdicts.** The Cagan hyperinflation criterion is `PENDING_EVAL` ("count-based threshold requires event log; data not sufficient to auto-count") in both hyperinflation-titled runs, and a GLF recovery metric is `PENDING_EVAL` due to "threshold expression unparseable by regex". Verdicts emit anyway.
- **X7. Mechanical / unfalsifiable specifications in pcw100.** Decision rule "expected-sign coefficient with two-sided p<0.10 is SUPPORTED" applied to near-mechanical constructions (minimum-wage bite ratio → p10 wage, R²=0.975) and to cross-sectional EFW quartile contrasts with sign expectations only.

---

## Claim-by-claim audit

### 1. `west_east_germany_economic_system_divergence_1950_1989` — supported, 11/11
**Citation:** `engine/runs/west_east_germany_economic_system_divergence_1950_1989/result_card.md`; `HYPOTHESIS_FRAMEWORK_AUDIT.md` §E7.
- Metric 2 `consumer_goods_availability_wait_time` observed = 100 (1985) vs threshold ">10" — a round-number sentinel consistent with X2, not a documented wait-time series.
- The basket counts treatment-defining attributes as outcomes: `stasi_surveillance_intensity` is part of the GDR regime definition, not an outcome of it; including it makes the pattern match partly tautological. Claim text promises metrics "each drawn from a different publisher or methodology family" — unverified and, per X3, demonstrably false in the sister Soviet run.
- Verdict migrated from §E7 inconclusive with no ledger (X5).
**Classification:** method flaw (sentinel value, circular metric); scope mismatch (institutional attributes counted as outcome channels).
**Proposed v2 spec:** split the basket into (a) outcome metrics only (GDP pc, consumer goods, emigration, environment, post-1990 revealed productivity) and (b) regime-coding checks excluded from the count; require per-metric publisher sha256 diversity attestation in diagnostics; emit an audit record for the 100-sentinel metric.

### 2. `north_south_korea_development_divergence_1953_present` — supported, 11/12
**Citation:** `engine/runs/north_south_korea_development_divergence_1953_present/result_card.md`.
- Metric 6 `famine_episode_count`: "PRK has 40 (2020); threshold >=1" — 40 famine events in a single year is a data-glitch signature (event-log row count, not documented famines). The metric passes on a corrupted count.
- Metric 1's 40.25× GDP ratio rests on DPRK estimates that §E7 flagged as pending `bank_of_korea_dprk_estimates`; the card gives no publisher provenance per metric.
- Metric 9 `PENDING_DATA` ("No KOR observations in loaded vintages") does not gate the verdict (X6-adjacent).
**Classification:** data gap (DPRK provenance); method flaw (event-count glitch scored MET).
**Proposed audit record:** re-derive metric 6 from a named famine chronology; require publisher field per metric row on the card before the support count is computed.

### 3. `cuba_socialist_economy_stagnation_1960_2023` — supported, 7/10 (exactly at threshold)
**Citation:** `engine/runs/cuba_socialist_economy_stagnation_1960_2023/result_card.md`.
- Verdict sits exactly on the support boundary (7 of 10, threshold 7). One of the 7 METs is metric 3 with observed = 100 (1993) — the X2 sentinel. Remove one sentinel-driven MET and the verdict flips to partial/refute territory. The framework's own E1 lesson (fragile compound rules) is repeated here in count form.
- Metric 1's NOT_MET notes reveal threshold miscalibration: LatAm peer median 2023/1960 ratio was 2.916 against a required >3.0 — the comparator benchmark itself failed, meaning the divergence bar was set above what the region actually did; and the Cuba ratio used "2018/1960" while the threshold says 2023 (endpoint substitution).
- Metric 2: "CUB rank in 1958 = 73 (top 5 required)" — a rank of 73 in a ~20-country LatAm frame is a pipeline artefact (global rank fed into a regional-rank test).
**Classification:** method flaw (sentinel, endpoint substitution, wrong-universe rank); convenient threshold (support lands exactly on boundary via a sentinel metric).
**Proposed v2 spec:** boundary-margin rule — if verdict margin ≤ 1 metric and any MET metric carries a sentinel/fallback stat name, emit `partial` with a disclosed fragility note.

### 4. `soviet_union_central_planning_gdp_collapse_1989_1991` — supported, 9/10
**Citation:** `engine/runs/soviet_union_central_planning_gdp_collapse_1989_1991/result_card.md`, `diagnostics.json:28,66,126,174-178`.
- `gdp_contraction_peak_to_trough` observed_value = 99.99999929185707 (diagnostics.json:28) — impossible value scored MET (X2). Consensus estimate is ~40%.
- Unit mismatches (X1): `life_expectancy_male_collapse` threshold ">5 year decline" evaluated against an 11.56 *percent* decline stat; `fertility_collapse_tfr` threshold ">0.5 decline in TFR" evaluated against a 98.2 *percent* decline; `poverty_headcount_surge` threshold ">20 percentage point" evaluated against a 6.98 *percent*-increase stat (yielding a spurious NOT_MET — the one honest-looking failure is itself a unit error).
- Duplicate sha256 across four "independent" publishers (X3) voids the card's independence claim.
- Window stretch: claim is "1989–1991 collapse" but metrics run to 1996–1999 — the scored event is the 1990s transition depression, not the 1989–91 plan collapse; these are distinct causal stories (the card's own claim conflates them).
**Classification:** method flaw (sentinels, unit mismatch, hash collision); scope mismatch (window/title vs scored event).
**Proposed audit record:** full unit-typetag audit of every canonical metric: store `threshold_unit` and `stat_unit` in diagnostics and hard-fail on mismatch. This run should be re-scored after the fix, not silently patched.

### 5. `great_leap_forward_famine_output_collapse_1959_1961` — supported, 8/10
**Citation:** `engine/runs/great_leap_forward_famine_output_collapse_1959_1961/result_card.md`.
- Metric 10 `PENDING_EVAL`: "threshold expression unparseable by regex" — the evaluation harness could not parse its own pre-registered threshold (X6).
- Metric 1 uses `max_in_window_fallback` = 36M excess deaths — the *maximum* of an estimate range (scholarly range ~15–45M) selected by a fallback rule. Choosing max-of-range is a disclosed-prior-shaped convenience: any fallback that takes the extreme of a contested estimate range should be declared as such on the card.
- Metric 7 `NOT_MET` with observed 0 for provincial dispersion — absence of provincial data scored as absence of dispersion.
**Classification:** data gap (provincial mortality, parse failure); method flaw (max-of-range fallback); convenient threshold (fallback convention favors support).
**Proposed v2 spec:** contested-estimate metrics must carry `estimate_range: [low, high]` and score against the *median* published estimate, with sensitivity reported at low/high.

### 6. `zimbabwe_hyperinflation_land_reform_output_collapse_2000_2009` — supported, 8/10
**Citation:** `engine/runs/zimbabwe_hyperinflation_land_reform_output_collapse_2000_2009/result_card.md`.
- Metric 1 — the Cagan hyperinflation threshold, the namesake phenomenon of the hypothesis — is `PENDING_EVAL` (X6). A hypothesis titled "hyperinflation" was supported without its defining metric being evaluated.
- Metric 3 unit mismatch: `event-count [max_value] = 81829` (raw tonnes) compared against a ">50% decline" threshold (X1).
- Metric 8 (expropriation share) `PENDING_DATA` on `manual:utete_commission_report_2003`, `manual:buka_report_2002` — manual publishers never landed; this is exactly the §E7 fetcher debt, yet the run no longer reports inconclusive (X5).
**Classification:** method flaw (PENDING_EVAL core metric, unit mismatch); data gap (manual commission reports).
**Proposed audit record:** verdict-gating rule — if any metric tagged `definitional: true` is PENDING_EVAL/PENDING_DATA, verdict caps at `partial`. Record applies to claims 6, 7, and 2.

### 7. `venezuela_chavismo_canonical_case_multi_metric` — supported, 9/10
**Citation:** `engine/runs/venezuela_chavismo_canonical_case_multi_metric/result_card.md`.
- Cagan hyperinflation metric again `PENDING_EVAL` (X6).
- Unit mismatches (X1): metric 1 emigration threshold ">15% of 2013 population" scored against `pct_increase_from_baseline` = 120; metric 8 threshold ">=3 documented nationwide blackouts" scored against `pct_increase_from_baseline` = 50. Counts and population shares replaced by percent-growth stats.
- Verdict migrated from §E7 inconclusive with no ledger (X5); note the sibling hypothesis `venezuela_chavismo_framework_validation` landed `weakened` on pre-trend (§E2) — the multi-metric card route achieves "supported" for the same real-world episode with no identification at all, which the scoreboard treats as the stronger evidence tier.
**Classification:** method flaw; scope mismatch (pattern-match verdict outranks the identified DiD route on the scoreboard).
**Proposed v2 spec:** tier label on scoreboard: canonical pattern-match verdicts must render as `supported (descriptive)` and score below identified estimates for the same claim.

### 8. `banking_crisis_2008_gfc_canonical_multimetric` — supported, 7/7
**Citation:** `engine/runs/banking_crisis_2008_gfc_canonical_multimetric/result_card.md` (metric 1 note lists 254 "countries" incl. WLD/EUU/OED and a leading empty code), `manifest.yaml`.
- X4 in full: every metric was evaluated against the global panel, not the 9 named advanced economies. 254 entities with ≥4% peak-to-trough GDP declines in 2007–2014, including China and India, indicates the drawdown stat itself is misfiring (any local max-to-min within a 7-year window). Region aggregates double-count their members.
- The pre-registered rule "at least 5 of 9 countries" is unfalsifiable as implemented: with 254 entities scanned, any threshold is met somewhere.
**Classification:** method flaw (harness evaluated the wrong universe; aggregate double-count); public-claim overreach if cited as "the canonical 9-country GFC signature confirmed".
**Proposed v2 spec:** the metric evaluator must accept `sample: [USA, GBR, IRL, ISL, ESP, …]` from the hypothesis and count only those units; add a regression test asserting count ≤ sample size.

### 9. `pcw100_global_efw_trade_freedom_gdp_growth` — SUPPORTED
**Citation:** `engine/runs/pcw100_global_efw_trade_freedom_gdp_growth/result_card.md`.
- Cross-sectional OLS, 163 obs, quartile contrast, p=0.0015. Reverse causality (rich, fast-growing economies liberalize trade) and level-vs-growth endogeneity are unaddressed; the card itself admits "associational screen" yet emits the same SUPPORTED verdict the scoreboard treats as evidence. Decision rule requires only sign + p<0.10 (X7).
- Quartile composition embeds the conclusion: low-policy group is disproportionately conflict/fragile states (SYR, LBY, SDN, ZWE, VEN); the screen mostly re-measures state failure.
**Classification:** scope mismatch (associational screen scored at full evidentiary weight); method flaw (no temporal ordering or fragility controls in a pre-registered "expected sign" test).
**Proposed v2 spec:** pcw100 screens emit `screen_positive`/`screen_negative`, converted to SUPPORTED/REFUTED only after a follow-on identified run; scoreboard weights screens at ≤0.25.

### 10. `pcw100_us_mw_bite_ratio_p10_wage` — SUPPORTED
**Citation:** `engine/runs/pcw100_us_mw_bite_ratio_p10_wage/result_card.md`.
- Mechanical identity: bite ratio = MW/median wage; in high-bite states the p10 wage *is* the minimum wage. R²=0.975 with state/year indicators confirms near-identity, not an estimated effect. The hypothesis is unfalsifiable as constructed — a violation of the framework's own falsification-first standard.
- Quartile lists overlap: HI, MA, MD, MS, NY appear in *both* low-policy and high-policy groups. A unit in both extreme quartiles is a pipeline bug that invalidates the contrast.
**Classification:** method flaw (mechanical specification; overlapping contrast groups).
**Proposed audit record:** quartile-membership uniqueness check across all pcw100 runs (this bug likely generalizes — see claim 19's SOM anomaly); re-run with non-mechanical treatment (e.g. MW increases as events, outcome = p10 *relative to p50*).

### 11. `oecd_pdb_gdp_hour_frontier_convergence_1950_2025` — SUPPORTED
**Citation:** `engine/runs/oecd_pdb_gdp_hour_frontier_convergence_1950_2025/result_card.md`.
- `frontier_gap_lag` beta = 3.099: a coefficient >1 on a lagged *level* gap predicting *growth* implies the gap closes ~3× per year — a units/normalization red flag (gap likely expressed as ratio where 1 = 100 log-points, so the headline number is 100× misread on the card).
- This is β-convergence with the frontier on the RHS — mechanically, (frontier growth − own growth) vs own gap invites the same Solow-artefact collinearity the framework itself flagged in E1 for `asian_convergence_vs_western_stagnation_2000_2023`, where the identical econometric structure was declared a tooling bug when it produced a verdict the authors disliked. The framework cannot call the same artefact a bug in one run and support in another.
**Classification:** method flaw (asymmetric treatment of an acknowledged artefact); convenient threshold (no robustness spec registered).
**Proposed audit record:** cross-run consistency rule — any econometric structure formally declared an artefact in an archived verdict (see `asian_convergence_vs_western_stagnation_2000_2023/ARCHIVED_v1/`) must be flagged wherever it recurs, in either direction.

### 12. `banking_crisis_japan_1990_lost_decade` — supported, 4/5
**Citation:** `engine/runs/banking_crisis_japan_1990_lost_decade/result_card.md`.
- The one metric that directly measures the banking channel — `bank_npl_ratio_peak` — is `PENDING_DATA` ("No JPN observations in window 1998-2003"). Support for a *banking-crisis* hypothesis rests on asset prices, GDP, and an external crisis coding, with zero bank-balance-sheet data. Support threshold 4/5 was calibrated so that the missing core metric cannot block the verdict.
**Classification:** data gap (NPL series); convenient threshold (basket sized so the missing definitional metric is non-binding).
**Proposed v2 spec:** definitional-metric gating as in claim 6; add FSA/BOJ NPL vintages to the fetcher queue with this run ID as the unlocking consumer.

### 13. `vietnam_doi_moi_growth_human_development_1990_2023` — supported, 4/4
**Citation:** `engine/runs/vietnam_doi_moi_growth_human_development_1990_2023/result_card.md`.
- All four thresholds are one-sided trend descriptions (growth ≥4%, U5M decline ≥60%, openness ≥150%, services ≥35%) that most successful 1990–2023 developing economies meet. The claim is framed as a policy episode ("post-Doi Moi development path") but tested as "did Vietnam develop?" — no counterfactual, no comparator, no pre-Đổi-Mới baseline in the falsification rule. Nothing in the test could have failed given any WDI vintage of the last decade; prior ≈ 1.0 undisclosed.
**Classification:** scope mismatch (descriptive trend test scored as policy-episode evidence); convenient thresholds.
**Proposed v2 spec:** add comparator set (CHN, KHM, LAO, IND) with a divergence threshold and a 1976–1986 baseline metric; disclose prior per the §E6 convention ("included for framework validation").

### 14. `ethiopia_prewar_growth_human_development_2000_2019` — supported, 4/4
**Citation:** `engine/runs/ethiopia_prewar_growth_human_development_2000_2019/result_card.md`.
- Window selection is post-hoc: ending the sample in 2019 excludes the Tigray-war collapse, which is the strongest single observation against the "growth model" framing. A pre-registered window chosen *after* the war began is disclosed nowhere on the card.
- Metric 1 rests on Ethiopian official national accounts, whose growth figures are publicly contested (independent re-estimates put 2004–2019 growth several points below official). No alternative-estimate robustness metric exists.
**Classification:** data gap (contested source, no robustness series); convenient threshold/window (war exclusion).
**Proposed v2 spec:** window must be justified at pre-registration with a break-rule ("ends at first year of documented civil conflict"); add a dual-source GDP metric (official vs independent re-estimate) requiring agreement within 2pp.

### 15. `banking_crisis_greece_2010_2018_doom_loop` — supported, 6/6
**Citation:** `engine/runs/banking_crisis_greece_2010_2018_doom_loop/result_card.md`.
- Unit mismatches (X1): metric 2 threshold ">=19 pp rise (peak >= 27%)" scored against `pct_increase_from_baseline` = 1.43e+03; metric 3 threshold ">=175% of GDP" scored against `max_in_window_fallback` = 4.94e+04 — a 49,400 value for a debt-to-GDP ratio is a sentinel/wrong-series artifact scored MET.
- The doom-loop claim is a *propagation* mechanism (sovereign → bank holdings → recap → output), but all six metrics are co-occurring state variables; no holding-exposure or bank-sovereign correlation metric tests the loop itself. The verdict confirms a crisis happened, not the loop.
**Classification:** method flaw (sentinels, unit mismatch); scope mismatch (mechanism untested).
**Proposed v2 spec:** add an exposure metric (domestic-bank GGB holdings / bank assets ≥ threshold at program onset) and a sequencing metric (sovereign spread widening precedes bank CDS widening).

### 16. `south_korea_growth_health_services_shift_1990_2023` — supported, 4/4
**Citation:** `engine/runs/south_korea_growth_health_services_shift_1990_2023/result_card.md`.
- Same template as claims 13, 14, 20 with per-country tweaked thresholds. The claim contains no contestable proposition: "combined sustained real income growth, large child-mortality reductions, rising life expectancy, and a services-employment shift" is true of essentially every upper-middle-income country 1990–2023, so the supported verdict is guaranteed ex ante and injects scoreboard credit to whichever schools link the hypothesis (canonical-basket dimension missing: no inequality, household-debt, or work-intensity metric that could discriminate between schools' readings of the Korean model — household debt >100% of GDP and among-OECD-worst old-age poverty are unmeasured second-order dimensions).
**Classification:** scope mismatch (unfalsifiable basket; missing second-order/canonical dimensions).
**Proposed v2 spec:** template baskets must include ≥2 metrics on which schools' predictions diverge (e.g. household-debt ratio, relative old-age poverty, hours worked); growth-health templates without a discriminating metric are capped at `supported (descriptive)`.

### 17. `oecd_pdb_post_2008_productivity_hysteresis_panel` — SUPPORTED
**Citation:** `engine/runs/oecd_pdb_post_2008_productivity_hysteresis_panel/result_card.md`.
- `lp_growth ~ post_2008 + C(country)`: a level-shift dummy with no pre-trend control. OECD productivity growth was decelerating from ~2000 (well documented); attributing the post-2008 level to "hysteresis" (a causal permanence claim about crisis damage) without a pre-2008 trend term or a 2020–2024 COVID-window treatment misattributes a trend break to an event.
- No second-order dimensions: no sector decomposition (the slowdown is heavily ICT-sector and measurement-driven), no capital-deepening split — despite `oecd_pdb_capital_deepening_without_tfp_limit` existing in the same run family.
**Classification:** method flaw (no pre-trend control; COVID window unhandled); scope mismatch (trend deceleration scored as crisis-hysteresis evidence).
**Proposed v2 spec:** `lp_growth ~ post_2008 + trend_post_2000 + covid_dummies + C(country)`; hysteresis verdict requires the post-2008 dummy to survive the trend term.

### 18. `banking_crisis_asian_financial_crisis_1997_panel` — supported, 5/5
**Citation:** `engine/runs/banking_crisis_asian_financial_crisis_1997_panel/result_card.md`.
- X4 again: metric 1 counts 62 countries with ≥30% depreciation in 1997–1998 (including AUT, BEL, CAN, DEU — no such depreciations occurred; the stat is picking up cross-rate or unit-of-account artifacts), metric 2 counts 167 with ≥5% GDP declines. The pre-registered test was "at least 4 of 5 named countries"; the harness counted the world (incl. WLD, EUU aggregates) and would pass on any threshold.
- IMF-programme metric (the one metric correctly restricted to the named five) shows what the run should have looked like for all metrics.
**Classification:** method flaw (wrong evaluation universe; implausible counts).
**Proposed audit record:** same sample-restriction regression test as claim 8; flag all `banking_crisis_*_panel` runs for re-scoring (Brazil PROER, Nordic, etc. likely share the harness).

### 19. `pcw100_global_efw_sound_money_gdp_growth` — SUPPORTED
**Citation:** `engine/runs/pcw100_global_efw_sound_money_gdp_growth/result_card.md`.
- High-sound-money quartile contains SOM (Somalia) alongside CHE and SGP; low quartile contains VNM, the era's fastest grower. A top-quartile sound-money coding for a state without a functioning monetary authority signals an index/coding or missing-data-imputation problem in the input, not a meaningful contrast.
- EFW sound money is dominated by recent inflation history; growth collapses *cause* inflation (fiscal monetization under stress), so the expected-sign screen is reverse-causal by construction (X7).
**Classification:** method flaw (reverse causality by construction); data gap (quartile membership integrity — SOM coding).
**Proposed audit record:** input-integrity spot check of EFW quartile membership for all pcw100 runs; publish the imputation rules behind conflict-state EFW scores.

### 20. `india_growth_health_services_shift_1990_2023` — supported, 4/4
**Citation:** `engine/runs/india_growth_health_services_shift_1990_2023/result_card.md`.
- Per-country threshold drift across the template family: growth bar is 3.5% for Korea, 4.0% for India, 5.0% for Ethiopia — each set just below the realized value (4.28, 4.47, 5.87 respectively). Thresholds that track realized outcomes this closely are calibrated post-hoc; the margin distribution (0.78, 0.47, 0.87 pp) across three countries is the signature of convenient thresholds.
- India's 2011-12 base-year revision raised measured GDP growth by ~1.5–2pp on contested methodology; no dual-vintage robustness metric. Services-employment bar (≥30%) sits below the level India's ~34% already reached, while agriculture still employs ~43% — "services shift" is scored on a threshold that does not discriminate structural transformation from stasis.
**Classification:** convenient threshold (post-hoc calibration signature); data gap (base-year revision controversy unaddressed).
**Proposed v2 spec:** template thresholds must be set from a cross-country rule (e.g. upper-quartile of the country's income peer group), fixed once in `_axis_index.yaml`, not per-country; add dual-vintage GDP sensitivity metric.

---

## Classification tally
- **Method flaw (10):** claims 1, 3, 4, 6, 7, 8, 10, 11, 15, 18 (with 5, 9, 17, 19 as secondary).
- **Data gap (4 primary):** claims 2, 5, 12, 14 (secondary in 6, 19, 20).
- **Scope mismatch (5 primary):** claims 9, 13, 16, 17 (and 1, 7, 15 secondary).
- **Public-claim overreach (2):** claim 8 (if cited as 9-country confirmation); the family-wide "independent data sources" interpretation line (X3) wherever it ships on public cards.

## Standing proposals (no implementation performed by this review)
1. **Audit record A (unit typetag):** store `threshold_unit` / `stat_unit` per metric; hard-fail mismatch. Blocks X1. Affected runs: 3, 4, 6, 7, 15 (minimum confirmed set).
2. **Audit record B (sentinel scan):** flag any observed value ≥ 99.99 for `peak_to_trough_pct_decline` or ≥ 1e+04 for ratio-type metrics. Blocks X2.
3. **Audit record C (provenance diversity):** assert distinct sha256 across a metric's declared sources. Blocks X3.
4. **Audit record D (sample restriction):** canonical panel metrics count only pre-registered units; regression test count ≤ sample size. Blocks X4.
5. **Audit record E (verdict-migration ledger):** any verdict change from `inconclusive`/`refuted` requires an archived prior card + ledger entry, matching the `ARCHIVED_v1_false_refuted` precedent. Blocks X5.
6. **Audit record F (definitional gating):** metrics tagged definitional must gate verdicts at `partial` when PENDING_*. Blocks X6.
7. **v2 spec family (evidentiary tiers):** pcw100 screens and pattern-match canonicals emit tiered verdicts (`screen_positive`, `supported (descriptive)`) weighted below identified estimates on the scoreboard.

Gate remains human. This review produced no code, no edits, and no verdict changes; all fixes above are proposals for the Hardener/implementer lanes.
