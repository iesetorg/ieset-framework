# Batch 03 OECD PDB readiness and run audit

- PDB vintage: `data/vintages/oecd/DSD_PDB@2026-05-12T133454Z.parquet`
- PMR vintage: `data/vintages/oecd_pmr/OECD.ECO.GCRD_DSD_PMR_DF_PMR_1.2@2026-05-04T194708Z.parquet`
- Available PDB vintages: 2
- Existing PDB runners detected before Batch 03 exclusion: 9
- Promoted and run: 8 of 10
- Blocked as registered: 2 of 10

## Inventory

PDB vintages:
- `data/vintages/oecd/DSD_PDB@2026-05-05T200750Z.parquet`
- `data/vintages/oecd/DSD_PDB@2026-05-12T133454Z.parquet`

Existing PDB runners detected:
- `engine/runs/eu_regulatory_burden_productivity_drag`
- `engine/runs/gdpr_digital_sector_firm_scale_effect`
- `engine/runs/industrial_concentration_labour_share_link`
- `engine/runs/labour_reform_greece_2010_2014_troika_internal_devaluation`
- `engine/runs/oecd_product_market_deregulation_tfp_panel`
- `engine/runs/uk_real_wage_stagnation_2008_present_decomposition`
- `engine/runs/us_eu_gdp_per_capita_divergence_policy_causes`
- `engine/runs/wage_inflation_spiral_post_2021_oecd_panel`
- `engine/runs/wfh_productivity_panel_2020_2024`

## Completed
- `oecd_pdb_gdp_hour_frontier_convergence_1950_2025`: SUPPORTED (n=1122, countries=31)
- `oecd_pdb_tfp_growth_frontier_persistence_1970_2025`: REFUTED_OR_WEAK (n=468, countries=17)
- `oecd_pdb_capital_deepening_without_tfp_limit`: SUPPORTED (n=483, countries=17)
- `oecd_pdb_small_open_economy_frontier_convergence`: SUPPORTED (n=527, countries=14)
- `oecd_pdb_market_reform_productivity_compounder`: REFUTED_OR_WEAK (n=31, countries=31)
- `oecd_pdb_hours_reduction_output_tradeoff_panel`: SUPPORTED (n=1113, countries=31)
- `oecd_pdb_post_2008_productivity_hysteresis_panel`: SUPPORTED (n=859, countries=31)
- `oecd_pdb_public_sector_share_productivity_drag`: REFUTED_OR_WEAK (n=990, countries=31)

## Blockers
- `oecd_pdb_investment_share_tfp_interaction_panel`: BLOCKED_MISSING_SERIES; missing `oecd_pdb:investment share / gross fixed capital formation share in OECD PDB`. Latest OECD PDB vintage has capital services and capital-deepening measures, but no investment-share/GFCF-share measure needed by the registered id.
- `oecd_pdb_tax_wedge_productivity_growth_panel`: BLOCKED_MISSING_SERIES; missing `oecd:OECD.CTP.TPS,DSD_TAX@DF_TAX_WAGES_COMP,2.1`. No OECD tax-wage/tax-wedge parquet vintage is present under data/vintages/oecd.
