# Monthly Hypothesis Throughput Batch 03

Date: 2026-05-12

Purpose: continue the monthly hypothesis throughput plan in 30-run batches, using promoted hypotheses with repaired replication wrappers.

## Summary

- Runs attempted: 30
- Verdict-bearing results: 28
- Supported: 17
- Partial: 1
- Refuted: 10
- Inconclusive data/model-pending: 2

## Results

| Hypothesis | Result |
| --- | --- |
| `net_migration_revealed_preference_market_institutions` | refuted |
| `hayek_regulatory_uncertainty_investment_chilling` | refuted |
| `medical_migration_market_opportunity` | supported |
| `economic_freedom_corruption_decline` | supported |
| `bukele_fiscal_trajectory_tax_cuts_imf_2019_2024` | refuted |
| `market_reform_inflation_adjusted_wages` | refuted |
| `market_freedom_consumption_pc_1970_2024` | supported |
| `regulatory_transparency_investment` | supported |
| `market_governance_qol_broad_scope` | supported |
| `debt_overhang_private_investment_30yr` | supported |
| `sea_thailand_2014_coup_tourism_shock` | refuted |
| `price_signal_distortion_capital_misallocation` | partial |
| `public_procurement_innovation_conditions` | supported |
| `intervention_intensity_qol_volatility_1970_2024` | supported |
| `market_entry_uniform_code_productivity` | refuted |
| `female_lfp_market_opportunity` | supported |
| `procurement_competition_corruption` | supported |
| `labor_reform_real_wage_growth` | supported |
| `gm_crop_adoption_yield_convergence` | supported |
| `regulatory_predictability_cross_sector_investment` | refuted |
| `frontier_income_volatility_state_allocation` | refuted |
| `campaign_favoritism_subsidy_allocation` | supported |
| `health_savings_account_preventive_spending` | supported |
| `gfc_balance_sheet_recession_post_2008_household_dual_mandate` | inconclusive data/model-pending |
| `housing_tax_distortion_mobility` | refuted |
| `licensing_discretion_bribery` | supported |
| `dialysis_market_competition_outcome_quality` | inconclusive data/model-pending |
| `sea_philippines_bpo_industrial_policy_2005_2024` | supported |
| `venture_capital_market_depth_innovation` | refuted |
| `banking_crisis_laeven_valencia_predictors_panel` | supported |

## Repair Queue

- `gfc_balance_sheet_recession_post_2008_household_dual_mandate`: treatment has no within-country variation under country fixed effects.
- `dialysis_market_competition_outcome_quality`: treatment proxy has no within-country variation under country fixed effects.

## QA Notes

- Multiple broad governance / corruption / quality-of-life hypotheses reuse common panel structure and in some cases produce identical coefficient fingerprints. These should be treated as valid run outputs but not promoted to scoreboard weight until the evidence packet confirms that the hypothesis-specific treatment and outcome are actually distinct.
- The refuted results are useful for narrowing broad claims. Batch 03 in particular suggests several "market institutions always improve X" phrasings need better conditioning on outcome, lag, sector, or institutional baseline before scoreboard mapping.
