# New Data Hypothesis Unlock Plan — 2026-05-12

## Daily rate-limited automation

Created active Codex cron automation `daily-rate-limited-data-backfill`.

- Schedule: daily at 03:15 local time.
- Workspace: `.`.
- Target: retry official-source pulls that are blocked by daily API limits or very large public files.
- Priority order: BLS LAU state unemployment / employment-population panels, narrowed QCEW state totals, filtered Eurostat migration, OECD catalogue-repaired ALMP/pensions/house-prices/government-expenditure pulls.
- Output expectation: write manifests/audits, preserve vintages, summarize rows, source URLs, failures, and hypothesis blockers. Do not commit or push.

## Fresh data landed in this wave

The 2026-05-12 mega wave added roughly 9.9 million rows of new official-source data.

| Source | Rows | Main use |
|---|---:|---|
| BIS `WS_CREDIT_GAP` | 24,356 | Credit boom, credit gap, crisis-prediction, financial-fragility tests |
| BIS `WS_DSR` | 7,050 | Household/corporate debt-service stress |
| BIS `WS_SPP` | 35,388 | Real residential property prices |
| BIS `WS_EER` | 1,196,431 | Real/nominal effective exchange-rate panels |
| OECD `DSD_SOCX@DF_SOCX_AGG` | 3,060,473 | Welfare spending, unemployment benefits, stabilisers |
| OECD `EPL_OV` | 1,123 | Employment-protection strictness |
| OECD `DSD_LMS_low_education_unemployment_rate` | 926,337 | Low-skill labour-market outcomes |
| OECD `DSD_PDB` | 1,734,430 | Productivity, unit labour cost, GDP/hour, TFP-adjacent panels |
| Eurostat `nama_10_gdp` | 1,100,189 | GDP and macro aggregates |
| Eurostat `nama_10_a10` | 869,177 | Sectoral value-added and reallocation |
| Eurostat `une_rt_a` | 39,669 | EU unemployment |
| Eurostat `lfsa_egan` | 414,005 | Employment by activity |
| Eurostat `ilc_di12` | 870 | Income distribution slices |
| Eurostat `nrg_pc_205` | 79,560 | Industrial and household electricity prices |
| BLS `QCEW_county_NAICS722_employment_panel` | 35,770 | US food-service employment, minimum-wage robustness |
| BLS `QCEW_state_NAICS722_employment_panel` | 561 | US state food-service employment |
| ILOSTAT unemployment / LFP / wages | 376,966 | Labour-market controls and wage channels |
| WDI agricultural exports | 15,000 | Agriculture/trade hypotheses |

## Loader repairs made

Added narrow source bridges in `scripts/run_panel_fe.py`.

- `ilostat:EAR_4MTH_SEX_RT` now resolves to `ilostat:EAR_EHRA_SEX_NB_A`.
- `ilostat:unemployment_rate` now resolves to `ilostat:UNE_2EAP_SEX_AGE_RT_A`.
- OECD PDB canonical URNs now resolve to the local `oecd:DSD_PDB` vintage.
- OECD SOCX canonical URNs now resolve to the local `oecd:DSD_SOCX@DF_SOCX_AGG` vintage.
- BIS `WS_CREDIT_GAP` now recognises `BORROWERS_CTY` as the country column.
- BIS `WS_CREDIT_GAP` now slices `CG_DTYPE=C` for gap variables and `CG_DTYPE=B` for credit-to-GDP level/change variables.

## Verdicts unlocked immediately

| Hypothesis | Before | After | Meaning |
|---|---|---|---|
| `abct_credit_boom_predicts_capital_misallocation_oecd` | data pending | `SUPPORTED` | BIS credit booms now load and the coefficient is positive and significant. |
| `private_credit_growth_crisis_predictor_oecd` | data pending | `PARTIAL` | Direction is positive, but p=0.225, so the broad claim is not decisive under current FE design. |

## Refresh reruns completed

| Hypothesis | Refreshed verdict | Meaning |
|---|---|---|
| `bis_credit_gap_house_price_reversal_panel` | `supported` | Fresh BIS credit-gap and house-price vintages still support the reversal claim. |
| `bis_household_dsr_credit_slowdown_panel` | `refuted` | Fresh BIS DSR/credit data do not support the registered slowdown claim. |
| `bis_household_dsr_unemployment_surge_panel` | `partial` | Direction/evidence is mixed after refresh. |
| `gfc_endogenous_minsky_leverage_mechanism` | `SUPPORTED` | 3 of 4 Minsky indicators passed under the refreshed data path. |

## Rerun queue

These are worth rerunning or upgrading next because the new data closes a real blocker.

1. `financial_deregulation_crisis_vulnerability` — committed verdict exists, but now has better BIS credit-gap visibility for robustness.
2. `demo_mexico_fertility_decline_wages` — ILO wage source is now visible, but the current generic panel has only 22 complete observations; needs narrower controls or a bespoke country-year design.
3. `demo_eastern_europe_outmigration_wages` — now has Eurostat sectoral accounts plus ILO wage alias; existing committed verdict should be checked against fresh vintages.
4. `oecd_product_market_deregulation_tfp_panel` — OECD PDB now visible, but PMR treatment is time-invariant under country FE; needs estimator redesign.
5. `us_eu_gdp_per_capita_divergence_policy_causes` — OECD PDB now visible for GDP/hour outcome.
6. `uk_real_wage_stagnation_2008_present_decomposition` — OECD PDB growth vintage now visible.
7. `industrial_concentration_labour_share_link` — OECD PDB source now visible; still needs concentration treatment.
8. `universal_vs_meanstest_child_poverty` — SOCX now visible; still needs explicit interaction variable.
9. `unemployment_benefit_generosity_employment_drag` — fresh SOCX and ILO unemployment.
10. `nuclear_phaseout_energy_cost_industry_exit` — fresh Eurostat electricity prices; still needs IEA/ENTSO-E/FDI pieces for full spec.
11. `nuclear_phaseout_grid_reliability_cost_tradeoff` — still pending because outcomes are currently constructed/IEA/ENTSO-E, not Eurostat-only; candidate for a narrower electricity-price-only sibling.
12. `minimum_wage_disemployment_at_high_bite_ratios` — QCEW and OECD low-education unemployment visible; still blocked by state/subnational bite data gate.

## First 30 new hypotheses to promote from this data

These should be drafted as clean, public-facing, testable claims using the landed data instead of waiting for more scraping.

1. `bis_credit_gap_predicts_house_price_reversal_oecd_1970_2025` — high credit gaps predict weaker 3-5 year real house-price growth.
2. `bis_credit_to_gdp_growth_predicts_credit_slowdown_oecd_1970_2025` — rapid credit/GDP expansion predicts later credit contraction.
3. `bis_dsr_threshold_unemployment_surge_oecd_1999_2025` — high household DSR predicts unemployment increases.
4. `bis_dsr_threshold_consumption_slowdown_oecd_1999_2025` — high household DSR predicts household-consumption slowdown.
5. `bis_reer_appreciation_export_slowdown_panel_1964_2025` — real exchange-rate appreciation predicts export-share deterioration.
6. `bis_reer_overvaluation_current_account_reversal_panel_1964_2025` — REER overvaluation predicts current-account repair through demand compression.
7. `oecd_social_spending_unemployment_persistence_panel_1980_2024` — higher unemployment-benefit spending predicts slower unemployment normalisation.
8. `oecd_social_spending_automatic_stabiliser_output_loss_panel_1980_2024` — higher social spending cushions GDP drawdowns during recessions.
9. `oecd_family_benefits_child_poverty_tradeoff_panel_1980_2024` — family-benefit spending predicts lower child poverty where data coverage permits.
10. `oecd_public_social_spending_employment_rate_tradeoff_panel_1980_2024` — larger social-spending share predicts lower employment rates after controls.
11. `oecd_epl_strictness_low_education_unemployment_panel_1985_2019` — stricter employment protection predicts higher low-education unemployment.
12. `oecd_epl_strictness_youth_unemployment_panel_1985_2019` — stricter employment protection predicts higher youth unemployment.
13. `oecd_low_education_unemployment_minimum_wage_bite_panel_1981_2024` — higher minimum-to-median wage ratios predict higher low-education unemployment.
14. `bls_qcew_food_service_minimum_wage_border_panel_2014_2024` — higher local minimum wages predict lower county food-service employment growth.
15. `bls_qcew_food_service_state_minimum_wage_panel_2014_2024` — state minimum-wage hikes predict lower NAICS 722 employment growth.
16. `oecd_pdb_productivity_frontier_gap_market_reform_panel_1950_2025` — market reform episodes predict faster GDP/hour convergence.
17. `oecd_pdb_unit_labour_cost_competitiveness_panel_1950_2025` — rising unit labour costs predict export-share deterioration.
18. `oecd_pdb_labour_productivity_social_spending_tradeoff_1980_2024` — large welfare states show weaker productivity growth unless openness is high.
19. `oecd_pdb_services_productivity_gap_panel_1950_2025` — services-heavy economies show slower aggregate productivity growth.
20. `eurostat_sectoral_reallocation_growth_eu_1995_2025` — faster sectoral reallocation predicts higher GDP/hour growth.
21. `eurostat_industry_share_electricity_price_exit_panel_2007_2025` — higher industrial electricity prices predict manufacturing-share decline.
22. `eurostat_household_electricity_price_energy_poverty_panel_2007_2025` — higher household electricity prices predict worse distributional stress.
23. `eurostat_energy_price_nuclear_share_panel_2007_2025` — nuclear-retaining countries have lower industrial electricity prices after controls.
24. `eurostat_unemployment_sectoral_shift_panel_1995_2025` — faster sectoral transition predicts short-run unemployment spikes.
25. `ilostat_lfp_social_spending_panel_1990_2027` — higher social spending predicts lower prime-age participation only in high-benefit regimes.
26. `ilostat_wage_growth_labour_market_tightness_panel_1990_2025` — low unemployment predicts faster nominal wage growth.
27. `ilostat_wage_growth_trade_openness_panel_1990_2025` — trade openness predicts higher wage growth in high-productivity countries.
28. `wdi_agricultural_export_share_trade_policy_panel_1960_2025` — higher agricultural export dependence predicts greater sensitivity to trade restrictions.
29. `bis_house_price_credit_gap_minsky_cycle_panel_1970_2025` — house-price booms amplify credit-gap crisis risk.
30. `bis_credit_gap_policy_rate_interaction_panel_1970_2025` — credit gaps are more predictive of later stress when policy rates are low in real terms.

## Processing strategy

1. Run the BIS refresh batch first. It has the cleanest landed source coverage and should produce the fastest verdicts.
2. Promote the Eurostat electricity-price sibling tests rather than forcing the current nuclear reliability spec to pretend it has ENTSO-E reliability data.
3. Split minimum-wage work into two tracks: a US QCEW food-service employment track that is runnable now, and a daily-limited LAU/OEWS track that the automation keeps filling.
4. Treat OECD PDB as a hypothesis factory. It can support long-horizon productivity, GDP/hour, labour-cost, and sectoral-reallocation tests with much broader coverage than the earlier developmentalist short-window cases.
5. Keep every new hypothesis readable: one plain-English claim, one policy lever, one outcome, one falsification rule, and one short “what this proves / does not prove” note.
