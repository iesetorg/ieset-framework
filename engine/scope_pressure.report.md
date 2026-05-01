# Scope Pressure Audit

- Total specs: **580**
- Profiled large-scope specs: **249**

## Country-count buckets
- `1`: 168
- `2`: 13
- `3-5`: 63
- `6-10`: 170
- `11-20`: 110
- `21+`: 56

## Large-scope unresolved specs by template
- `panel_fe`: 83
- `did_callaway_santanna`: 23
- `synthetic_control`: 18
- `synth_did`: 16
- `panel_fe_decomposition`: 14
- `descriptive`: 12
- `local_projections`: 10
- `event_study`: 8
- `multi_metric_checklist`: 4
- `lp_iv`: 2
- `cointegration_vecm`: 2
- `iv_2sls`: 1
- `unknown`: 1

## Top downscope candidates

| hypothesis_id | template | sample_n | covered_countries | joint_rows | verdict | recommendation |
|---|---:|---:|---:|---:|---|---|
| liberal_free_trade_partner_growth_panel_1990_2020 | did_callaway_santanna | 61 | 0 | 0 | inconclusive | Replace broad panel framing with compact regional core countries. |
| liberal_capital_account_openness_growth_premium_panel | panel_fe | 59 | 0 | 0 | inconclusive | Replace broad panel framing with compact regional core countries. |
| economic_freedom_index_income_correlation | panel_fe | 44 | 0 | 0 | inconclusive | Replace broad panel framing with compact regional core countries. |
| austrian_rent_seeking_concentration_olson_growth_drag | panel_fe | 36 | 0 | 0 | inconclusive | Replace broad panel framing with compact regional core countries. |
| ordo_competition_law_enforcement_growth_premium_oecd | panel_fe | 36 | 0 | 0 | inconclusive | Replace broad panel framing with compact regional core countries. |
| banking_crisis_laeven_valencia_predictors_panel | panel_fe | 34 | 0 | 0 | inconclusive | Replace broad panel framing with compact regional core countries. |
| demo_ageing_pension_burden_cross_country | panel_fe | 30 | 0 | 0 | inconclusive | Replace broad panel framing with compact regional core countries. |
| demo_life_expectancy_lfp_panel | panel_fe | 30 | 0 | 0 | inconclusive | Replace broad panel framing with compact regional core countries. |
| demo_marriage_age_fertility_growth | panel_fe_decomposition | 30 | 0 | 0 | inconclusive | Replace broad panel framing with compact regional core countries. |
| colonial_institutions_post_independence_growth | panel_fe | 29 | 0 | 0 | inconclusive | Replace broad panel framing with compact regional core countries. |
| eu_ets_emissions_reduction_vs_1p5c_pathway | descriptive | 27 | 0 | 0 | inconclusive | Rewrite as single-country descriptive spec. |
| eu_green_deal_vs_ets_emissions_mechanism | event_study | 27 | 0 | 0 | inconclusive | Rewrite as single-country ITS or treated-vs-few-controls event study. |
| resource_rent_capture_outperforms_laissez_faire | panel_fe | 27 | 0 | 0 | inconclusive | Replace broad panel framing with compact regional core countries. |
| financial_macroprudential_ltv_dsti_credit_panel | did_callaway_santanna | 26 | 0 | 0 | inconclusive | Replace broad panel framing with compact regional core countries. |
| demo_gender_pay_gap_oecd_evolution | panel_fe | 25 | 0 | 0 | inconclusive | Replace broad panel framing with compact regional core countries. |
| demo_education_attainment_wage_premium_panel | panel_fe | 25 | 0 | 0 | inconclusive | Replace broad panel framing with compact regional core countries. |
| austrian_savings_rate_investment_quality_link | panel_fe | 24 | 0 | 0 | inconclusive | Replace broad panel framing with compact regional core countries. |
| universal_healthcare_cost_outcome_oecd | panel_fe | 23 | 0 | 0 | inconclusive | Replace broad panel framing with compact regional core countries. |
| private_credit_growth_crisis_predictor_oecd | panel_fe | 23 | 0 | 0 | inconclusive | Replace broad panel framing with compact regional core countries. |
| working_time_reduction_employment_neutral_oecd | panel_fe | 23 | 0 | 0 | inconclusive | Replace broad panel framing with compact regional core countries. |

## Notes
- `covered_countries` uses outcome-treatment overlap for panel-style specs and outcome coverage for descriptive specs.
- These are rewrite/downscope candidates, not automatic spec edits.
