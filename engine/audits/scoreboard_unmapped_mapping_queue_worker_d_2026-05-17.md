# Scoreboard Unmapped Mapping Queue - Worker D

Generated: 2026-05-17

## Scope

Worker D reviewed the current position and hypothesis mapping surface against:

- `engine/audits/scoreboard_prediction_outcome_audit_2026-05-17_unblocking_batch.md`
- `engine/audits/graduation_high_quality_batch7_2026-05-17.md`
- `engine/audits/replication_wrapper_backfill_2026-05-17_unblocking.md`
- `positions/*.yaml`
- `hypotheses/**/*.yaml`
- `schemas/position.schema.json`

The pass looked for tested, public-scoreboard-eligible verdicts that have replication wrappers and diagnostics but no clean `covers_claims` / position coverage.

## Summary

- Reviewed backfill/unblocking candidates: 25.
- Already cleanly mapped in the current tree: 14 hypotheses / 27 claim-link pairs.
- Tested but unmapped candidates from the reviewed batch: 11 hypotheses.
- New mappings applied by Worker D: 0.
- Scoreboard swing from this file: 0 raw net / 0 q-net.

No claim-link patch was made because every unmapped candidate below fails at least one safety gate: duplicate of an already mapped sister hypothesis, weak or neutral partial verdict, too broad a panel to assign school credit, or no clear school-level falsifiable claim rather than a descriptive plumbing fact.

## Already Clean In Current Tree

These reviewed hypotheses already have reciprocal position-side links and hypothesis-side `covers_claims` entries. Worker D did not duplicate them.

| hypothesis | clean links | note |
| --- | ---: | --- |
| `abenomics_monetary_policy_demand_effect` | 1 | Batch 7 graduate; mapped to `post_keynesian`. |
| `universal_vs_meanstest_child_poverty` | 1 | Batch 7 graduate; mapped to `social_democratic`. |
| `china_renewables_global_learning_curve_spillover` | 3 | Mapped to developmental/green-public-planning claims. |
| `automatic_stabiliser_2008_contraction_severity` | 1 | Mapped to `social_democratic`. |
| `fiat_expansion_erodes_currency_purchasing_power_long_run` | 3 | Mapped to Austrian, Chicago monetarist, classical liberal claims. |
| `labour_market_reform_almp_complementarity_effect` | 1 | Mapped to `empirical_pragmatist`. |
| `tcja_2017_growth_effect` | 1 | Mapped to `new_keynesian` as mixed. |
| `universal_healthcare_cost_outcome_oecd` | 1 | Mapped to `social_democratic`. |
| `demo_mexico_fertility_decline_wages` | 3 | Mapped narrowly to demographic-dividend claims. |
| `export_openness_agricultural_diversification` | 3 | Mapped to agricultural market-access/upgrading claims. |
| `india_extra_aadhaar_upi_productivity` | 2 | Mapped to digital public infrastructure claims. |
| `minimum_wage_youth_unemployment_tradeoff` | 2 | Mapped to youth minimum-wage tradeoff claims. |
| `nuclear_phaseout_accident_risk_reduction_value` | 2 | Mapped to nuclear-risk valuation claims. |
| `startup_density_frontier_prosperity` | 3 | Mapped to entrepreneurship/competition claims. |

## Precise Queue - Do Not Map Yet

| hypothesis | verdict | evidence | why mapping is not safe now | safe next step |
| --- | --- | --- | --- | --- |
| `central_bank_balance_sheet_cpi_decoupling_panel_2008_2020` | WEAKENED | associational | Duplicates already mapped QE surfaces (`qe_base_money_cpi_transmission_failure`, `qe_asset_inflation_vs_cpi_divergence_post_2008`). Current result is USA-heavy and missing the intended cross-institution gates. Mapping to MMT/Post-Keynesian/Chicago now would double-count the same QE thesis. | Wait for Japan/ECB/BoE gates or explicitly supersede one older QE claim-link set in a dedicated migration. |
| `demo_ageing_pension_burden_cross_country` | PARTIAL, direction inconclusive | associational | Broad OECD ageing/pension elasticity does not cleanly cover Ordoliberal Bismarckian-vs-universal architecture claims, and the verdict is neutral. | Build an architecture-comparison hypothesis or tag it as neutral coverage only if a position claim is rewritten to broad PAYGO pension burden. |
| `demo_brazil_demographic_transition_inequality` | PARTIAL, direction inconclusive | associational | Brazil inequality decline is overdetermined; no existing position claim isolates the demographic-transition share. Mapping would create a weak broad-panel-style claim. | Add a narrow Brazil demographic-transition claim only after decomposition gates identify a material demographic share. |
| `financial_fed_reverse_repo_facility_usage_2021_2024` | SUPPORTED | descriptive | This is a monetary-operations fact about ON RRP peak/decline, not a clean school prediction. No current school claim makes the RRP level itself a falsifiable proposition. | Keep as context unless a school-specific liquidity-management claim is authored before observing the result. |
| `japan_sargent_wallace_refutation_1990_2024` | WEAKENED | descriptive | Duplicates the already mapped `japan_public_debt_solvency_inflation_independence` MMT claim. The newer result is also weakened by debt-vintage/CPI coverage caveats. | Treat as a possible replacement only in a deliberate MMT monetary-sovereignty migration, not an additive mapping. |
| `monopoly_capital_concentration_markup_link` | PARTIAL, direction inconclusive | associational | Potentially relevant to Marxian monopoly-capital claims and Ordoliberal concentration claims, but current coefficient is wrong-signed/insignificant. Mapping would only add weak neutral coverage and risks over-crediting a broad proxy. | Wait for industry-level concentration/markup data or a directional verdict. |
| `private_credit_growth_crisis_predictor_oecd` | PARTIAL, direction inconclusive | associational | Potential Post-Keynesian/Minsky surface, but AUC and Laeven-Valencia gates are not clean; verdict is neutral. | Repair distress-event data and AUC threshold before mapping to Minsky financial-instability claims. |
| `quality_adjusted_consumption_market_liberal_panel` | PARTIAL, direction inconclusive | associational | Broad market-liberal consumption panel has weak proxy construction and no decisive verdict; existing market-freedom consumption mappings already cover narrower tested surfaces. | Do not map until quality-adjustment proxy is made auditable and verdict becomes directional. |
| `tax_inequality_brazil_tax_base_evolution` | PARTIAL, claim direction not auto-inferred | descriptive | Direction is not auto-inferred, and the hypothesis mixes tax-base, transfer, and Brazilian political episodes. Mapping to social-democratic or fiscal-progressivity claims would be ambiguous. | Add explicit decomposition outputs for transfer-side vs tax-progressivity attribution before any school mapping. |
| `usd_issuer_solvency_no_default_post_1971` | WEAKENED | descriptive | Duplicates the already mapped `us_dollar_issuer_solvency_record` MMT claim. The new candidate has missing CDS/auction gates and is necessary-but-not-sufficient for the broader MMT claim. | Treat as a replacement candidate only if the old hypothesis is retired or migrated. |
| `welfare_transfer_us_arpa_expanded_ctc_2021` | WEAKENED | causal | ARPA/CTC poverty claims are already mapped through `tax_inequality_biden_ctc_2021_child_poverty`, which is tested and supported. This newer event-study candidate is weakened by missing monthly CPSP and parental-LFP gates. | Do not add duplicate links unless the older CTC hypothesis is explicitly superseded. |

## Patch Decision

No position or `covers_claims` edits are recommended in this pass. The clean scoreboard action is to leave the 11 unmapped candidates in queue and avoid manufacturing extra tested coverage from weak broad-panel or duplicate sister hypotheses.

## Suggested Validation Commands

Use no-write validation for link/scope checks so shared audit artifacts are not rewritten:

```bash
python3 -c 'import importlib.util; spec=importlib.util.spec_from_file_location("v","scripts/validate_link_reciprocity.py"); v=importlib.util.module_from_spec(spec); spec.loader.exec_module(v); p=v.load_positions(); h=v.load_hypotheses(); rows=v.check_forward(p,h)+v.check_reverse(p,h); errors=[r for r in rows if r["level"]=="ERROR"]; warns=[r for r in rows if r["level"]=="WARN"]; print("link_reciprocity errors={} warnings={}".format(len(errors),len(warns))); raise SystemExit(1 if errors else 0)'
python3 -c 'import importlib.util; spec=importlib.util.spec_from_file_location("v","scripts/validate_scope_alignment.py"); v=importlib.util.module_from_spec(spec); spec.loader.exec_module(v); rows,stats=v.validate_all(); errors=[r for r in rows if r["level"]=="ERROR"]; warns=[r for r in rows if r["level"]=="WARN"]; print("scope_alignment pass={} errors={} warnings={}".format(stats.get("pass",0),len(errors),len(warns))); raise SystemExit(1 if errors else 0)'
python3 scripts/audit_scoreboard_outcomes.py --out /private/tmp/worker_d_scoreboard_after_queue
```
