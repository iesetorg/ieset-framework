# Swarm 2026-05-22: 200-Hypothesis Factory Master Index

## Purpose

This is the controller index for the 200-candidate hypothesis swarm. The source
shards hold the full claims, variable sketches, likely data sources, school
coverage notes, and runability flags. This file records the integration QA and
turns the swarm output into a practical run plan.

The design principle is the same as the prior long-horizon market/state waves:
test measured policies, institutions, prices, quantities, and outcomes; never
use school labels as data. Results can later support or refute schools only
after replication, evidence-packet review, and careful `covers_claims` mapping.

## Source Shards

| lane | file | count | focus |
| --- | --- | ---: | --- |
| A | `engine/audits/swarm_2026-05-22_200_hypotheses_worker_A_market_liberal.md` | 50 | classical liberal, Austrian, Chicago, ordoliberal, institutional market mechanisms |
| B | `engine/audits/swarm_2026-05-22_200_hypotheses_worker_B_left_intervention.md` | 50 | social democratic, democratic socialist, Marxian, MMT, post-Keynesian, degrowth, eco-socialist claims tested fairly |
| C | `engine/audits/swarm_2026-05-22_200_hypotheses_worker_C_state_capacity_mixed.md` | 50 | developmentalism, institutional capacity, macro/fiscal conditionality, public goods, crisis response |
| D | `engine/audits/swarm_2026-05-22_200_hypotheses_worker_D_sectoral_data_rich.md` | 50 | near-term sectoral panels using OECD, BIS, WDI, PWT, WITS, WIPO, Eurostat, OWID, ILOSTAT |

## Integration QA

| check | result |
| --- | ---: |
| Total numbered candidates | 200 |
| Unique candidate IDs | 200 |
| Duplicate IDs inside swarm | 0 |
| Collisions with existing `hypotheses/*/*.yaml` IDs | 0 |
| Worker files with exactly 50 numbered candidates | 4/4 |
| Runability flags present | 200/200 |

Readiness split:

| status | count | action |
| --- | ---: | --- |
| `READY_NOW` | 85 | promote the cleanest to YAML specs and first-pass panel/event runs |
| `NEEDS_ALIAS` | 57 | add local alias/crosswalk/filter work before running |
| `NEEDS_DATA` | 58 | data-hunt queue for specialized policy, event, ownership, micro, or regulatory panels |

## School Coverage

The combined batch deliberately touches every tracked school:

- Market-liberal / market-order: `classical_liberal`, `austrian`, `chicago_monetarism`, `ordoliberal`, `institutionalism`.
- State-capacity / mixed: `developmentalism`, `new_keynesian`, `post_keynesian`, `mmt`, `empirical_pragmatist`.
- Left / interventionist: `social_democratic`, `democratic_socialist`, `market_socialist`, `marxian`, `marxist_leninist`, `eco_socialist`, `degrowth`.

`empirical_pragmatist` remains a benchmark/control lens, not an ideological
score target.

## Immediate Run Queue

These are the strongest first candidates for the next 30-40 run wave because
they are `READY_NOW`, use familiar source families, and have clear scoreboard
interpretation paths after replication.

### Market-Liberal / Market-Order

1. `ml_money_growth_nominal_anchor_inflation_1960_2024`
2. `ml_central_bank_independence_inflation_real_wage_panel`
3. `ml_financial_repression_savings_real_rate_investment`
4. `ml_tariff_reduction_consumer_real_income_panel`
5. `ml_product_market_regulation_tfp_growth_oecd`
6. `ml_expropriation_risk_private_investment_panel`
7. `ml_employment_protection_youth_unemployment_duration`
8. `ml_carbon_pricing_command_control_cost_per_ton`
9. `ml_market_reform_package_qol_long_horizon_synth`
10. `ml_rule_bound_regulation_investment_volatility`

### Left / Interventionist Tests

11. `redistribution_gap_bottom40_real_income_growth_oecd`
12. `progressive_tax_top_income_share_and_growth_oecd`
13. `public_health_spending_avoidable_mortality_panel`
14. `minimum_wage_bite_low_pay_poverty_employment_panel`
15. `labor_share_demand_growth_wage_led_panel`
16. `capital_controls_crisis_volatility_growth_panel`
17. `austerity_after_recession_hysteresis_panel`
18. `fossil_subsidy_phaseout_emissions_poverty_tradeoff_panel`
19. `material_footprint_wellbeing_decoupling_high_income_panel`
20. `financialization_labor_share_investment_panel`

### State Capacity / Conditionality

21. `capacity_stabilizers_output_loss_threshold_oecd`
22. `capacity_tax_revenue_public_goods_threshold`
23. `capacity_government_effectiveness_state_size_nonmonotonic`
24. `capacity_rule_of_law_financial_depth_productive_allocation`
25. `capacity_trade_liberalization_institutional_variance`
26. `capacity_education_spending_learning_threshold`
27. `capacity_health_spending_mortality_corruption_interaction`
28. `capacity_tariff_sunset_infant_industry_upgrade`
29. `capacity_hightech_exports_government_effectiveness_interaction`
30. `capacity_corruption_public_investment_leakage`

### Data-Rich Sectoral Panels

31. `bis_credit_gap_house_price_unemployment_lag_panel`
32. `bis_household_dsr_policy_rate_consumption_slowdown_panel`
33. `wits_tariff_cuts_import_variety_consumption_panel`
34. `wipo_resident_patenting_tfp_followthrough_panel`
35. `owid_fossil_subsidy_energy_intensity_panel`
36. `oecd_minimum_wage_bite_low_education_unemployment_panel`
37. `wdi_out_of_pocket_health_spending_mortality_panel`
38. `tax_revenue_public_investment_growth_panel`
39. `government_consumption_private_investment_drag_panel`
40. `hightech_exports_product_concentration_growth_panel`

## Alias Repair Queue

The biggest alias repairs likely to unlock repeated runs:

1. OECD labour/welfare: TaxBEN replacement rates, participation tax rates,
   benefit cliffs, ALMP categories, EPL cells, collective bargaining coverage.
2. OECD/Eurostat housing: rent burden, social housing share, construction
   completions, permits, housing-cost overburden, homelessness proxies.
3. BIS/FRED monetary: policy-rate gaps, credit gaps, house-price interactions,
   DSR by household/corporate sector, asset-price/CPI divergence.
4. WITS/Comtrade: import variety, export product concentration, food tariffs,
   high-tech/manufacturing product baskets.
5. WIPO/OECD innovation: resident vs non-resident patenting, R&D intensity,
   patent follow-through into TFP and high-tech exports.

## Data-Hunt Queue

The largest `NEEDS_DATA` unlocks:

1. Ownership and governance panels: SOE shares, public utility ownership,
   state-owned banking assets, cooperative employment, codetermination laws.
2. Regulation/event panels: rent control strictness, zoning changes, parking
   minimum repeal, procurement openness, energy permitting delay, data
   localization rules.
3. Policy-event panels: nationalization, fuel-subsidy reform with transfer
   design, green public procurement, capital controls, job guarantee designs.
4. Micro/admin panels: occupational licensing, construction permits, municipal
   broadband, land-value taxation, property titling, firm productivity.

## Promotion Strategy

1. Promote 30-40 `READY_NOW` candidates into YAML specs in batches of 10.
2. Run first-pass panels only after each spec has a single primary treatment,
   a single primary outcome, and a clear falsification gate.
3. Keep broad-panel results out of the scoreboard until they have either a
   bespoke replication script or a defensible generic-runner interpretation.
4. Map to schools only after verdict review; avoid pre-shopping scoreboard
   effects. Position links and hypothesis-side `covers_claims` should be added
   together.
5. Treat `empirical_pragmatist` as a neutral benchmark/control when mapping.

## Notes

- Worker D initially duplicated the existing `bis_household_dsr_consumption_slowdown_panel` ID. The new candidate was renamed to `bis_household_dsr_policy_rate_consumption_slowdown_panel` before final QA.
- No hypothesis YAMLs, position files, run artifacts, or scoreboard mappings
  were created by this swarm. This is a planning/backlog wave only.
