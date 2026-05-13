# Batch 07-09 A4 welfare/labour/minimum-wage first-run audit

Run UTC: 2026-05-12T195529Z

## Tally

- Selected immediately runnable IDs: 10
- Successfully run IDs: 10
- Batch 07 run count: 2
- Batch 08 run count: 4
- Batch 09 run count: 4
- Blocked or deferred IDs noted: 4

## Results

| Rank | Hypothesis id | Batch | Verdict | N | Units | Coef | p |
| ---: | --- | --- | --- | ---: | ---: | ---: | ---: |
| 1 | `oecd_socx_public_social_spending_employment_tradeoff` | 07 | SUPPORTED | 2127 | 42 | -0.3638 | 0.0001 |
| 2 | `oecd_socx_open_economy_welfare_compatibility_panel` | 07 | PARTIAL | 2118 | 42 | 0.0021 | 0.0318 |
| 3 | `oecd_epl_low_education_unemployment_panel_1985_2019` | 08 | PARTIAL | 1301 | 36 | 0.8637 | 0.4538 |
| 4 | `oecd_low_education_unemployment_minimum_wage_bite` | 08 | REFUTED | 1094 | 28 | -0.9799 | 0.7970 |
| 5 | `oecd_activation_spending_low_education_unemployment` | 08 | REFUTED | 1290 | 36 | 0.3667 | 0.7041 |
| 6 | `oecd_epl_growth_shock_unemployment_persistence_panel` | 08 | REFUTED | 1482 | 37 | -0.4363 | 0.3978 |
| 7 | `bls_qcew_county_food_service_minimum_wage_growth` | 09 | REFUTED | 25228 | 2951 | 0.0389 | 0.0165 |
| 8 | `bls_qcew_state_food_service_minimum_wage_growth` | 09 | REFUTED | 510 | 51 | 0.0150 | 0.6293 |
| 9 | `bls_oews_median_bite_food_service_employment_panel` | 09 | REFUTED | 408 | 51 | 1.5833 | 0.4108 |
| 10 | `bls_minimum_wage_bite_low_tail_threshold_panel` | 09 | SUPPORTED | 408 | 51 | -0.2206 | 0.0840 |

## Blockers And Deferred

- `oecd_socx_unemployment_benefits_duration_panel`: SOCX aggregate vintage has unemployment compensation spending but no benefit-duration variable.
- `oecd_socx_tax_wedge_employment_compatibility_panel`: No OECD tax-wedge vintage was found in local data/vintages/oecd.
- `bls_qcew_county_food_service_wage_floor_border_design`: County adjacency/border-pair crosswalk is not landed locally.
- `bls_oews_p10_bite_food_service_employment_panel`: Runnable, but displaced by the low-tail threshold total-employment screen to keep the requested wave to ten IDs.

## Changed Run Paths

- `engine/runs/oecd_socx_public_social_spending_employment_tradeoff/`
- `engine/runs/oecd_socx_open_economy_welfare_compatibility_panel/`
- `engine/runs/oecd_epl_low_education_unemployment_panel_1985_2019/`
- `engine/runs/oecd_low_education_unemployment_minimum_wage_bite/`
- `engine/runs/oecd_activation_spending_low_education_unemployment/`
- `engine/runs/oecd_epl_growth_shock_unemployment_persistence_panel/`
- `engine/runs/bls_qcew_county_food_service_minimum_wage_growth/`
- `engine/runs/bls_qcew_state_food_service_minimum_wage_growth/`
- `engine/runs/bls_oews_median_bite_food_service_employment_panel/`
- `engine/runs/bls_minimum_wage_bite_low_tail_threshold_panel/`
