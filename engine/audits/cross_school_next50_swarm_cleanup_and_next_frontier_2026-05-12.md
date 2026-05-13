# Cross-School Next 50 Swarm Cleanup And Next Frontier - 2026-05-12

## Cleanup Status

- Generated wave size: 50 hypotheses, 50 steelmen, 50 run directories.
- Required run artifacts present for every run: `diagnostics.json`, `manifest.yaml`, `result_card.md`, `chart_data.json`, `coefficients.parquet`, `replication.py`.
- Verdict tally: 13 `SUPPORTED`, 25 `PARTIAL`, 12 `REFUTED`.
- Batch coverage: five batches of 10.
- School coverage: Austrian, classical liberal, Chicago monetarist, ordoliberal, developmentalist, Marxian, market socialist, post-Keynesian, MMT, social democratic, new Keynesian, eco-socialist, degrowth, empirical-pragmatist.

## Local Repairs Applied

- Added explicit `covers_claims: []` to every generated `cross_school_*` hypothesis YAML.
- Added `verdict_label` to every generated run manifest.
- Deduplicated controls before writing hypothesis YAML and result-card text, so cases where the outcome was also the default control no longer display duplicate controls.
- Added a real ISO3 country allowlist so World Bank aggregate region and income codes are excluded from the panels.
- Replaced truncated 80-country metadata samples with the full filtered country list.
- Corrected diagnostics so they report the deduplicated controls actually used in the model.
- Re-ran the full cross-school generator after these repairs.

## Verification

- `cross_school_*` targeted spec scan: no matching errors.
- Scope alignment: 2313 pass, 0 errors, 6 warnings.
- Local structural checks:
  - 50 unique hypothesis IDs.
  - 50 steelman links resolve.
  - 50 manifests match diagnostics verdicts.
  - 0 invalid ISO3 country codes in generated hypothesis samples.
  - 0 diagnostics list the outcome as its own control.
  - 0 missing run artifacts.

The full repository-wide schema validator still reports older corpus errors outside this wave. Those are not introduced by the cross-school batch.

## What The Swarm Found

The main issue is no longer raw school-count balance. It is weak-test balance: some schools are technically covered but represented by broad proxies that are too blunt for policy users.

Priority repairs:

1. Replace blunt fiscal-size tests with design-sensitive welfare and stabiliser tests.
2. Replace linear eco/degrowth energy tests with threshold and cost-of-transition designs.
3. Replace generic developmentalist state-capacity panels with capability, export-discipline, and sector-productivity tests.
4. Replace generic debt tests with currency-issuer, external-constraint, and fiscal-dominance threshold tests.
5. Build policy-treatment datasets so the policy browser can show tested policies, not just macro associations.

## Next 30 Testable Hypotheses

### Batch 1: Highest Priority Repairs

1. `oecd_socx_automatic_stabiliser_output_loss_panel_1980_2024`
2. `oecd_activation_vs_passive_support_low_skill_unemployment`
3. `mmt_currency_issuer_debt_inflation_threshold_panel`
4. `gfc_contraction_depth_liberalised_vs_state_managed_systems`
5. `energiewende_industrial_price_competitiveness_panel_2007_2025`
6. `us_eu_hours_worked_leisure_public_services_gap`
7. `institutional_quality_trade_liberalisation_variance`
8. `minimum_wage_bite_low_education_unemployment_panel`
9. `bis_credit_gap_dsr_joint_fragility_panel`
10. `nordic_welfare_institutional_quality_interaction`

### Batch 2: Policy-Legible Welfare, Labour, And Monetary Tests

11. `oecd_epl_youth_low_skill_dualism_panel_1985_2019`
12. `agenda2010_unemployment_duration_wage_tradeoff`
13. `macron_reforms_state_capacity_labour_outcomes`
14. `tax_revenue_poverty_vs_growth_tradeoff_panel`
15. `public_social_spending_employment_rate_tradeoff_open_economies`
16. `family_benefits_fertility_housing_cost_interaction`
17. `forced_saving_welfare_architecture_cpf_afp_vs_transfers`
18. `volcker_disinflation_institutional_preconditions_panel`
19. `gold_standard_long_run_inflation_volatility_tradeoff`
20. `zimbabwe_fiscal_dominance_property_rights_tax_base`

### Batch 3: Developmentalist And Institutional Capability

21. `korea_hci_export_capability_1961_1985_comparators`
22. `taiwan_itri_semiconductor_capability_spillover`
23. `government_effectiveness_hightech_threshold_panel`
24. `private_credit_hightech_threshold_vs_financialisation`
25. `sectoral_reallocation_productivity_eu_1995_2025`
26. `manufacturing_productivity_spillover_growth_panel`
27. `industrial_policy_governance_capacity_conditionality_upgrade`
28. `export_discipline_vs_import_substitution_growth`
29. `state_capacity_fdi_absorptive_capacity_panel`
30. `resource_rents_governance_growth_trap_panel`

## Highest-Leverage Policy Data Adds

1. World Bank WITS / UNCTAD TRAINS tariffs and NTMs.
   - Expected scale: 1M-20M product-country-year rows.
   - Unlocks: tariff liberalisation, import competition, industrial policy, export complexity.

2. UN Comtrade bulk trade flows.
   - Expected scale: 50M-300M+ rows at HS detail.
   - Unlocks: trade variety, import exposure, export concentration, sanctions, supply-chain exposure.

3. UNIDO INDSTAT plus fuller OECD STAN / EU KLEMS sector productivity.
   - Expected scale: 500k-5M rows.
   - Unlocks: sectoral TFP, manufacturing productivity, public-sector drag, industrial-policy persistence.

4. IMF Government Finance Statistics and OECD Revenue Statistics.
   - Expected scale: 500k-5M rows.
   - Unlocks: tax mix, fiscal capacity, austerity, public investment, redistribution versus growth.

5. World Bank Enterprise Surveys plus B-READY / Doing Business panels.
   - Expected scale: 200k+ firm rows plus country-year indices.
   - Unlocks: regulation, licensing, corruption, informality, entry barriers, credit constraints.

6. IMF/OECD/IEA fossil-fuel and energy-subsidy panels.
   - Expected scale: 50k-500k rows.
   - Unlocks: fuel-subsidy reform, energy-price distortions, industrial electricity costs, green industrial policy.

## Recommended Next Move

Run Batch 1 above before generating another broad 50. It directly improves the weak spots exposed by the latest verdict wave and uses data already present locally for most cases.

For data work, start with WITS/TRAINS and pair it with Comtrade-derived measures. That gives the policy database a real trade-policy spine and unlocks multiple schools at once.
