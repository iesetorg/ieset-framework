# Hypothesis Wave Cleanup Audit - 2026-05-22

## Scope

This audit covers the current uncommitted hypothesis work from the latest two
waves:

- 32 free-market / redistribution specs from
  `free_market_redistribution_spec_wave_2026-05-22.md`
- 13 data-hunt specs from `data_hunt_13_spec_campaign_2026-05-21T140210+0000`

Total real hypothesis scope: 45 specs.

The broader worktree remains intentionally dirty from other workstreams. This
audit does not classify unrelated data backfills, web edits, or older modified
run artifacts as part of this wave.

## Validation

Wave-local checks:

- 45/45 hypothesis YAML specs found.
- 45/45 steelman files found.
- 45/45 `engine/runs/<hypothesis_id>/diagnostics.json` files found.
- 45/45 `engine/runs/<hypothesis_id>/result_card.md` files found.
- Targeted hypothesis-schema validation for the 45 specs: pass.
- `git diff --check`: pass.

Global checks:

- `scripts/audit_runnability.py`: 1,657 total specs, 1,575 READY,
  82 NEEDS_DATA, 0 NEEDS_TEMPLATE, 0 LEGACY_SCHEMA, 1,657 HAS_RUN.
- Full `scripts/validate_specs.py`: fails with 482 pre-existing schema errors
  across 5,443 files. The observed failures are old corpus debt
  (`falsification.test` missing, empty country/outcome scopes, missing
  steelman fields, and position scope issues), not failures in this 45-spec
  wave.

## Verdict Tally

Combined 45-spec result:

| Verdict | Count |
| --- | ---: |
| SUPPORTED | 8 |
| PARTIAL | 19 |
| REFUTED | 6 |
| INCONCLUSIVE_DATA_PENDING | 12 |
| Total | 45 |

By wave:

| Wave | Supported | Partial | Refuted | Inconclusive | Total |
| --- | ---: | ---: | ---: | ---: | ---: |
| Free-market / redistribution 32 | 4 | 12 | 4 | 12 | 32 |
| Data-hunt 13 | 4 | 7 | 2 | 0 | 13 |

## Best Scoreboard Review Candidates

These have decisive first-pass results and clean enough framing to move into
manual claim-mapping review:

- `market_dynamism_government_consumption_investment_drag`
- `redistribution_public_consumption_tfp_drag_pwt_panel`
- `market_dynamism_regulatory_freedom_hightech_exports`
- `bis_corporate_dsr_manufacturing_drag_panel`
- `wits_export_concentration_hightech_drag_panel`
- `wipo_patent_applications_hightech_export_followthrough_panel`

Two additional supported results are usable but need extra care before mapping:

- `unconditional_transfer_work_hours_response_panel` because the generic runner
  grades a broad employment-rate outcome against a transfer proxy.
- `eurostat_unemployment_gini_stabilizer_panel` because it is a valid
  distribution/stabilizer channel but not a simple free-market score.

## Refutation Review Queue

These should be treated as real failed predictions unless a proxy/timing audit
finds a concrete reason to rerun:

- `redistribution_tax_private_investment_drag_panel`
- `market_dynamism_tariff_reduction_consumption_pc`
- `state_allocation_private_credit_innovation_panel`
- `redistribution_gini_compression_median_income_growth_oecd`
- `bis_credit_gap_governance_crisis_amplifier_panel`
- `bis_credit_gap_reer_appreciation_export_squeeze_panel`

The point of the system is that these count too. Do not relabel them as wins
without a documented specification repair.

## Repair Queue

The 12 inconclusive results cluster into four repair tracks:

1. OECD / ILOSTAT / TaxBEN labour data:
   `oecd_tax_wedge_low_wage_employment_penalty`,
   `temporary_contract_restrictions_youth_hiring_panel`,
   `oecd_taxben_benefit_cliff_lfp_penalty`,
   `in_work_benefits_low_income_employment_panel`,
   `activation_sanctions_reemployment_duration_panel`.
2. Mobility and distribution data:
   `redistribution_tax_transfer_mobility_oecd`.
3. Housing and construction data:
   `rent_price_controls_building_permits_eu_panel`,
   `construction_permit_burden_housing_output_panel`.
4. Treatment redesign / alias repair:
   `market_dynamism_entrepreneurial_entry_income_growth`,
   `business_freedom_employer_entry_employment_panel`,
   `price_control_intensity_electricity_access_growth_panel`,
   `price_signal_freedom_inflation_volatility_panel`.

## Commit Packaging

Clean wave package to stage when ready:

- The 45 hypothesis YAML files from the two waves.
- The 45 matching `hypotheses/steelman/*.md` files.
- The 45 matching `engine/runs/<hypothesis_id>/` run directories.
- Wave audit files:
  - `free_market_redistribution_spec_wave_2026-05-22.md`
  - `free_market_redistribution_run_wave_2026-05-22.md`
  - `free_market_redistribution_run_wave2_2026-05-22.md`
  - `data_hunt_13_spec_campaign_2026-05-21T140210+0000.*`
  - `data_hunt_13_spec_rerun_wave_2026-05-22.md`
  - this cleanup audit.
- `engine/runnability.derived.yaml` and `engine/runnability.report.md` if the
  commit is meant to include the refreshed runnability snapshot.

Do not bundle unrelated worktree changes into the same commit without a separate
review:

- `scripts/run_panel_fe.py`
- `scripts/automation_daily_rate_limited_backfill.py`
- `web/app/scoreboard/page.tsx`
- old modified run artifacts for unrelated hypotheses
- daily data-backfill manifests and audits
