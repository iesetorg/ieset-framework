# Second-wave legacy panel source-pair screen

Date: 2026-10-09. Fixed queue and preregistration snapshot: 19615241bdf76f630782e47eb19ca3dcedf50d23.

**Screening only. This report creates zero preregistrations, runs, or graduations.** Its 67 exact source-string pairs are an upper bound for manual design review, not 67 approved studies. Current graduation totals are in the conversion funnel.

The script reads the fixed review queue, index, and old spec metadata from Git. It does not open candidate data vintages, outcome values, null masks, or estimates. The separate five-case preregistration batch came later than this fixed snapshot.

## Funnel

| Screen | Count |
| --- | ---: |
| Legacy cases beyond first 500 | 820 |
| Basic panel records | 166 |
| Explicit old ISO3 rosters | 100 |
| Distinct exact source pairs before strict overlap | 78 |
| Pairs already in baseline strict registrations | 11 |
| Remaining exact source-pair groups | 67 |
| Old records within remaining groups | 88 |
| Duplicate old records grouped with a representative | 21 |
| Single-treatment/single-outcome source groups | 54 |

## Exclusion reasons

Counts overlap because one old case can fail several checks. Exact reasons for all 820 old IDs are in the companion CSV and JSON.

| Reason | Old records |
| --- | ---: |
| exact_pair_already_in_strict_registration | 12 |
| old_country_roster_not_explicit_iso3 | 66 |
| old_result_not_decisive_or_partial | 110 |
| risk_flag:estimator_floor_failure | 114 |
| risk_flag:falsification_rule_unsharpened | 20 |
| risk_flag:few_panel_units_review | 15 |
| risk_flag:integrity_or_correction_review | 36 |
| risk_flag:missing_variables | 252 |
| risk_flag:small_panel_sample_review | 4 |
| runner_not_run_panel_fe | 482 |
| template_not_panel_fe | 499 |

## Review flags within the 67 retained groups

These flags are not cleared by pair screening.

| Existing old-record flag | Pair groups |
| --- | ---: |
| old_evidence_packet_missing | 67 |
| old_manifest_missing | 67 |
| old_replication_missing | 24 |
| old_spec_requires_full_design_review | 67 |
| screening_or_proxy_design | 45 |

## All 67 exact source-pair groups

The first old ID in each group is a deterministic review representative, not a preferred result. Multiple old IDs in one row share the same exact treatment/outcome source sets and count once.

| Group | Treatment source set | Outcome source set | Old IDs (representative first) |
| --- | --- | --- | --- |
| pair_07d7a7b3f187 | wgi:RQ.EST | world_bank_wdi:SP.DYN.LE00.IN | market_freedom_life_expectancy_1970_2024, market_institutions_health_spending_efficiency |
| pair_0eccece4d1c8 | world_bank_wdi:GC.TAX.TOTL.GD.ZS | world_bank_wdi:SL.TLF.CACT.ZS | payroll_tax_labor_force_participation |
| pair_115eda0cb32a | wgi:RQ.EST | world_bank_wdi:NY.GDP.PCAP.KD.ZG | market_entry_uniform_code_productivity, market_institutions_material_wellbeing_resilience, market_institutions_qol_crisis_recovery, market_reform_qol_event_study_1980_2024 |
| pair_12e88633f48c | world_bank_wdi:SL.SRV.EMPL.ZS | world_bank_wdi:NE.CON.PRVT.PC.KD | private_sector_job_creation_consumption |
| pair_1b4cf147a04a | derived_trend:year_trend_2000_base | oecd_taxstruct:combined_corporate_income_tax_rate | tax_competition_corporate_rate_race_to_bottom |
| pair_22c23ff1fcf7 | world_bank_wdi:NY.GDP.PCAP.KD | world_bank_wdi:SE.SEC.CUAT.UP.ZS | market_income_school_completion |
| pair_2471f9b8850a | world_bank_wdi:NE.CON.GOVT.ZS | world_bank_wdi:TX.VAL.TECH.MF.ZS | incumbent_subsidy_innovation_drag, state_champion_tech_failure_rate |
| pair_27873a9f7bec | owid:consumption-subsidies-for-fossil-fuels | wits:high_tech_exports | owid_fossil_subsidy_hightech_export_drag_panel |
| pair_33a4d25e75f6 | world_bank_wdi:NE.CON.GOVT.ZS | world_bank_wdi:NY.GDP.PCAP.KD | state_allocation_capital_misallocation_living_standards, state_employment_share_productivity_drag, state_ownership_qol_drag_panel_1980_2024 |
| pair_35bdb0cd2a3a | wgi:RQ.EST | world_bank_wdi:SP.URB.TOTL.IN.ZS | market_urbanization_slum_reduction |
| pair_3a87a51015e1 | wgi:RQ.EST | world_bank_wdi:SM.POP.NETM | market_housing_supply_migration_opportunity, migration_labor_market_openness_qol |
| pair_3e6500a7bea8 | world_bank_wdi:GC.TAX.TOTL.GD.ZS | wgi:CC.EST | tax_complexity_trust_government |
| pair_3f170edaa20e | world_bank_wdi:NY.GDP.PCAP.KD | world_bank_wdi:SE.SEC.CUAT.UP.FE.ZS | market_reform_female_education |
| pair_3f94315681d9 | fraser_efw:efw_panel + world_bank_wdi:NE.CON.GOVT.ZS | wipo:patent_applications_resident + world_bank_wdi:FS.AST.PRVT.GD.ZS | state_allocation_private_credit_innovation_panel |
| pair_40628a0e25e2 | constructed: 1 for CHE from 1996 onward; NLD from 2006 onward; DEU from 1996 onward | world_bank_wdi:SH.DYN.MORT | market_healthcare_supply_mortality_amenable_panel |
| pair_414fa3a5eb22 | world_bank_wdi:NE.CON.GOVT.ZS | world_bank_wdi:NE.GDI.TOTL.ZS + world_bank_wdi:NY.GDP.PCAP.KD | market_dynamism_government_consumption_investment_drag |
| pair_49a78d22828c | bis:WS_CREDIT_GAP + bis:WS_EER | world_bank_wdi:NE.EXP.GNFS.KD.ZG | bis_credit_gap_reer_appreciation_export_squeeze_panel |
| pair_4a9b0a13f462 | oecd:DSD_SOCX@DF_SOCX_AGG + oecd:EPL_OV | oecd:DSD_LMS_low_education_unemployment_rate | oecd_almp_epl_low_education_unemployment_interaction_panel |
| pair_4d9076a3e641 | bis:WS_EER + world_bank_wdi:NE.TRD.GNFS.ZS | world_bank_wdi:FP.CPI.TOTL.ZG | bis_reer_appreciation_trade_open_disinflation_panel |
| pair_4dc898170899 | wgi:RQ.EST | world_bank_wdi:IS.RRS.PASG.KM | road_freight_liberalization_logistics_quality, transport_market_entry_commute_qol |
| pair_51f5e009f2f2 | bis:WS_DSR | world_bank_wdi:NV.IND.MANF.ZS | bis_corporate_dsr_manufacturing_drag_panel |
| pair_526c2f42e348 | world_bank_wdi:GC.TAX.TOTL.GD.ZS | world_bank_wdi:NE.GDI.FPRV.ZS | redistribution_tax_private_investment_drag_panel |
| pair_554656451c9a | constructed: 1 for USA from 1995 onward; GBR from 2000 onward; KOR from 2000 onward | world_bank_wdi:SH.XPD.CHEX.PC.CD | ophthalmology_laser_surgery_market_price_trajectory |
| pair_568d2a4abe54 | wgi:RQ.EST | world_bank_wdi:SE.SEC.ENRR | private_school_entry_education_quality |
| pair_60982b68c4b5 | world_bank_wdi:NE.TRD.GNFS.ZS | world_bank_wdi:NY.GDP.PCAP.KD | market_openness_multidimensional_prosperity_1995_2024 |
| pair_60a081af00ac | world_bank_wdi:NE.CON.GOVT.ZS | world_bank_wdi:EG.ELC.ACCS.ZS | state_monopoly_infrastructure_cost_overrun |
| pair_6682684242e6 | bis:WS_CREDIT_GAP + wgi:RQ.EST | world_bank_wdi:SL.UEM.TOTL.ZS | bis_credit_gap_governance_crisis_amplifier_panel |
| pair_6717a5758572 | wgi:RQ.EST | world_bank_wdi:SL.TLF.CACT.ZS | portable_benefits_market_flexibility |
| pair_6a82f723923f | world_bank_wdi:NE.CON.GOVT.ZS | wgi:GOV_WGI_VA.EST | state_planning_information_quality |
| pair_6d7e7038746f | wgi:RQ.EST | world_bank_wdi:SL.SRV.EMPL.ZS | price_signal_sectoral_reallocation_speed |
| pair_6f6c041b9e2d | eurostat:nrg_pc_205 | eurostat:une_rt_a | eurostat_power_cost_unemployment_slack_panel |
| pair_726678ccf11e | wgi:RQ.EST | world_bank_wdi:FP.CPI.TOTL.ZG | state_price_controls_real_consumption_shortage |
| pair_73c258f6c9ee | constructed: 1 for USA from 2000 onward; KOR from 2000 onward; EST from 2004 onward | world_bank_wdi:IT.NET.USER.ZS | platform_competition_dissipates_monopoly_rent |
| pair_761aba16c2ef | bis:WS_SPP | world_bank_wdi:NY.GDP.PCAP.KD | land_use_regulation_real_wage_drag |
| pair_76925820e328 | eurostat:une_rt_a | eurostat:ilc_di12 | eurostat_unemployment_gini_stabilizer_panel |
| pair_7b284e740c44 | constructed: 1 for USA from 1970 onward; DEU from 2015 onward; SWE from 1970 onward | bis:WS_SPP | rent_control_housing_supply_destruction_panel |
| pair_7cf6f8cb1936 | wits:tariff_average | wits:product_lines | wits_tariff_cuts_import_variety_panel |
| pair_80361e9943c0 | wgi:RQ.EST | world_bank_wdi:TX.VAL.TECH.MF.ZS | innovation_cluster_market_entry, market_competition_patent_quality, market_innovation_broad_scope, regulatory_sandbox_entry_innovation, university_spinout_market_rules |
| pair_80fd0371cdee | wgi:RQ.EST | bis:WS_SPP | housing_affordability_broad_scope_market, housing_supply_freedom_affordability |
| pair_85e13d875679 | constructed: 1 for USA from 1994 onward; GBR from 2000 onward; DEU from 2000 onward; IND from 2010 onward | world_bank_wdi:IT.NET.USER.ZS | spectrum_auction_vs_administrative_allocation_telecom |
| pair_86be023d6c3c | wgi:RQ.EST | world_bank_wdi:NE.CON.PRVT.PC.KD | market_freedom_consumption_pc_1970_2024 |
| pair_8acbde0bca90 | wits:weighted_mean_applied_tariff | world_bank_wdi:NE.CON.PRVT.PC.KD | market_dynamism_tariff_reduction_consumption_pc |
| pair_90194f90c1d4 | fraser_efw:efw_panel + wgi:RQ.EST | irena:installed_capacity_renewable | energy_market_competition_renewable_capacity_panel |
| pair_98551e034125 | wgi:GE.EST | world_bank_wdi:EG.ELC.ACCS.ZS | state_capacity_market_infrastructure_complement |
| pair_9ad6d1dc8153 | oecd:OECD.ELS.IMD,DSD_MIG@DF_MIG_EMP_EDU,1.0 + un_desa:international_migrant_stock | oecd:OECD.ELS.SAE,DSD_EARNINGS@DF_EARNINGS,1.0 | demo_migration_inflows_wages_skill_split |
| pair_9b287473d549 | fraser_efw:legal_system_property_rights | world_bank_wdi:NE.GDI.TOTL.ZS + world_bank_wdi:NY.GDP.PCAP.KD | market_dynamism_property_rights_investment_growth |
| pair_a25041091807 | wgi:RQ.EST | world_bank_wdi:NE.TRD.GNFS.ZS | port_competition_trade_cost |
| pair_a87cb7215868 | wgi:RQ.EST | world_bank_wdi:SE.TER.ENRR | human_capital_market_reform_lag |
| pair_aca18f2ed78a | world_bank_wdi:GC.TAX.TOTL.GD.ZS | world_bank_wdi:NE.GDI.FTOT.ZS | sector_neutral_tax_vs_exemption_cumulation |
| pair_b015c4120e59 | constructed: 1 for ARG from 2006 onward; ZWE from 2000 onward; ZMB from 1980 onward | world_bank_wdi:NV.AGR.TOTL.ZS | price_controls_food_output_decline_panel |
| pair_b40647366914 | eurostat:nrg_pc_205 | eurostat:nama_10_a10 | eurostat_power_cost_manufacturing_real_gva_panel |
| pair_c38681cb0258 | world_bank_wdi:NE.CON.GOVT.ZS | world_bank_wdi:NE.CON.PRVT.PC.KD | interventionist_subsidy_consumption_decay |
| pair_c5618dd6fcdc | world_bank_wdi:TX.VAL.TECH.MF.ZS | world_bank_wdi:NY.GDP.PCAP.KD | innovation_qol_market_spillovers |
| pair_c699a3c9ac62 | world_bank_wdi:NY.GDP.PCAP.KD | world_bank_wdi:SP.DYN.LE00.IN | market_income_channel_health_outcomes |
| pair_c9e7cbc37add | wgi:RQ.EST | world_bank_wdi:EG.ELC.ACCS.ZS | infrastructure_user_pricing_quality, private_generation_entry_electrification, urban_services_private_entry_quality, water_utility_private_participation_quality |
| pair_ca215910b630 | world_bank_wdi:FS.AST.PRVT.GD.ZS | pwt:rtfpna + world_bank_wdi:NY.GDP.PCAP.KD | market_dynamism_private_credit_productivity_growth |
| pair_cc7f01b8ed21 | wgi:GE.EST | world_bank_wdi:SE.TER.ENRR | tertiary_autonomy_research_output |
| pair_cf520cdd0ffa | wits:export_product_hhi_wits | wits:high_tech_exports | wits_export_concentration_hightech_drag_panel |
| pair_d1eab8e40b4a | wipo:patent_applications_resident | wits:high_tech_exports | wipo_patent_applications_hightech_export_followthrough_panel |
| pair_d1ec2ae3c834 | oecd:DSD_SOCX@DF_SOCX_AGG + wgi:GE.EST | world_bank_wdi:SL.EMP.TOTL.SP.ZS | oecd_socx_welfare_employment_capacity_interaction_panel |
| pair_df62056ce250 | wgi:RQ.EST | world_bank_wdi:SL.EMP.TOTL.SP.ZS | informality_entry_barriers_labor_qol, labor_market_flexibility_employment_qol, labor_market_market_qol_broad_scope, market_entry_small_business_jobs, market_reform_job_quality_panel |
| pair_e40a348d3077 | constructed: 1 for NZL from 2016 onward; USA from 2019 onward; JPN from 2002 onward | bis:WS_SPP | zoning_deregulation_housing_affordability |
| pair_e4a7f2759dba | wgi:RQ.EST | world_bank_wdi:NE.GDI.TOTL.ZS | public_procurement_innovation_conditions |
| pair_f0a853d6e4ef | heritage_ief:ief_panel + world_bank_wdi:FS.AST.PRVT.GD.ZS | irena:installed_capacity_renewable | market_dynamism_investment_freedom_renewables_diffusion |
| pair_f24eb0a76dea | world_bank_wdi:NE.TRD.GNFS.ZS | wipo:patent_applications_resident + world_bank_wdi:TX.VAL.TECH.MF.ZS | trade_openness_patent_diffusion_panel |
| pair_f3b24317be79 | wgi:RQ.EST | world_bank_wdi:SI.POV.DDAY | market_reform_poverty_exit_20yr |
| pair_fb93b4c9013d | world_bank_wdi:NY.GDP.PCAP.KD | world_bank_wdi:SH.MED.PHYS.ZS | medical_migration_market_opportunity |

## Interpretation limits and next step

- 67 exact source-string pairs are a screening upper bound, not 67 ready studies or graduations.
- A shared indicator under different aliases may still be a semantic duplicate; exact string matching does not settle this.
- An explicit old spec roster is not per-case historical fitted-row proof; each selected old run still needs a source and historical-runner audit.
- Many old records carry screening, proxy-design, missing-manifest, or missing-packet warnings even when they pass this coarse screen.
- Fresh v2 designs need narrowed direct claims, genuine unused holdouts, old-result disclosure, preregistration before outcome values, correction across tested families, exact replay, and no automatic school credit.
- This fixed snapshot precedes the separately committed five-case geographic-holdout batch and does not track later registrations or runs.

For each group, audit the old fitted-country boundary and source semantics, remove substantive duplicates and weak proxies, then write a narrower new-ID preregistration with a genuine holdout before inspecting candidate outcome values. A result needs exact replay and evidence-tier review before it counts as a graduation.
