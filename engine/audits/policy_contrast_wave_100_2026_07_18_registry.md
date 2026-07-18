# Policy Contrast Wave 100 — preregistration registry

- Wave date: 2026-07-18
- Hypotheses: 100
- Period constraint: every test is contained in 2006-2026
- Coefficients inspected before registration: **none**
- Decision rule: expected-sign p<0.10 = SUPPORTED; opposite-sign p<0.10 = REFUTED; otherwise PARTIAL
- Data-gate failure: INCONCLUSIVE and not graduated

## Cohorts

- `international_policy`: 50
- `us_fiscal_policy`: 20
- `us_minimum_wage`: 30

## Registered tests

| hypothesis | cohort | treatment | outcome | sign | n | units | contrast gap |
| --- | --- | --- | --- | :---: | ---: | ---: | ---: |
| `pcw100_us_mw_binding_premium_unemployment` | us_minimum_wage | binding_premium | unemployment | + | 969 | 51 | 1.75 |
| `pcw100_us_mw_binding_premium_employment_ratio` | us_minimum_wage | binding_premium | employment_ratio | - | 969 | 51 | 1.75 |
| `pcw100_us_mw_binding_premium_median_wage` | us_minimum_wage | binding_premium | median_wage | + | 459 | 51 | 2.79 |
| `pcw100_us_mw_binding_premium_p10_wage` | us_minimum_wage | binding_premium | p10_wage | + | 459 | 51 | 2.79 |
| `pcw100_us_mw_binding_premium_median_wage_growth` | us_minimum_wage | binding_premium | median_wage_growth | + | 306 | 51 | 2.715 |
| `pcw100_us_mw_binding_premium_food_employment_growth` | us_minimum_wage | binding_premium | food_employment_growth | - | 510 | 51 | 3.25 |
| `pcw100_us_mw_binding_premium_total_weekly_wage` | us_minimum_wage | binding_premium | total_weekly_wage | + | 102 | 51 | 6.415 |
| `pcw100_us_mw_binding_premium_food_weekly_wage` | us_minimum_wage | binding_premium | food_weekly_wage | + | 561 | 51 | 3.05 |
| `pcw100_us_mw_binding_premium_food_establishment_growth` | us_minimum_wage | binding_premium | food_establishment_growth | - | 510 | 51 | 3.25 |
| `pcw100_us_mw_binding_premium_poverty` | us_minimum_wage | binding_premium | poverty | - | 255 | 51 | 3.75 |
| `pcw100_us_mw_bite_ratio_unemployment` | us_minimum_wage | bite_ratio | unemployment | + | 459 | 51 | 0.09594 |
| `pcw100_us_mw_bite_ratio_employment_ratio` | us_minimum_wage | bite_ratio | employment_ratio | - | 459 | 51 | 0.09594 |
| `pcw100_us_mw_bite_ratio_median_wage` | us_minimum_wage | bite_ratio | median_wage | + | 459 | 51 | 0.09594 |
| `pcw100_us_mw_bite_ratio_p10_wage` | us_minimum_wage | bite_ratio | p10_wage | + | 459 | 51 | 0.09594 |
| `pcw100_us_mw_bite_ratio_median_wage_growth` | us_minimum_wage | bite_ratio | median_wage_growth | + | 306 | 51 | 0.09181 |
| `pcw100_us_mw_bite_ratio_food_employment_growth` | us_minimum_wage | bite_ratio | food_employment_growth | - | 408 | 51 | 0.1036 |
| `pcw100_us_mw_bite_ratio_total_weekly_wage` | us_minimum_wage | bite_ratio | total_weekly_wage | + | 102 | 51 | 0.2077 |
| `pcw100_us_mw_bite_ratio_food_weekly_wage` | us_minimum_wage | bite_ratio | food_weekly_wage | + | 459 | 51 | 0.09594 |
| `pcw100_us_mw_bite_ratio_food_establishment_growth` | us_minimum_wage | bite_ratio | food_establishment_growth | - | 408 | 51 | 0.1036 |
| `pcw100_us_mw_bite_ratio_poverty` | us_minimum_wage | bite_ratio | poverty | - | 153 | 51 | 0.1015 |
| `pcw100_us_mw_increase_event_unemployment` | us_minimum_wage | increase_event | unemployment | + | 969 | 51 | 1 |
| `pcw100_us_mw_increase_event_employment_ratio` | us_minimum_wage | increase_event | employment_ratio | - | 969 | 51 | 1 |
| `pcw100_us_mw_increase_event_median_wage` | us_minimum_wage | increase_event | median_wage | + | 459 | 51 | 1 |
| `pcw100_us_mw_increase_event_p10_wage` | us_minimum_wage | increase_event | p10_wage | + | 459 | 51 | 1 |
| `pcw100_us_mw_increase_event_median_wage_growth` | us_minimum_wage | increase_event | median_wage_growth | + | 306 | 51 | 1 |
| `pcw100_us_mw_increase_event_food_employment_growth` | us_minimum_wage | increase_event | food_employment_growth | - | 510 | 51 | 1 |
| `pcw100_us_mw_increase_event_total_weekly_wage` | us_minimum_wage | increase_event | total_weekly_wage | + | 102 | 51 | 1 |
| `pcw100_us_mw_increase_event_food_weekly_wage` | us_minimum_wage | increase_event | food_weekly_wage | + | 561 | 51 | 1 |
| `pcw100_us_mw_increase_event_food_establishment_growth` | us_minimum_wage | increase_event | food_establishment_growth | - | 510 | 51 | 1 |
| `pcw100_us_mw_increase_event_poverty` | us_minimum_wage | increase_event | poverty | - | 255 | 51 | 1 |
| `pcw100_us_fiscal_tax_revenue_share_poverty` | us_fiscal_policy | tax_revenue_share | poverty | - | 255 | 51 | 10.49 |
| `pcw100_us_fiscal_tax_revenue_share_median_income` | us_fiscal_policy | tax_revenue_share | median_income | + | 255 | 51 | 10.49 |
| `pcw100_us_fiscal_tax_revenue_share_employment_ratio` | us_fiscal_policy | tax_revenue_share | employment_ratio | + | 255 | 51 | 10.49 |
| `pcw100_us_fiscal_tax_revenue_share_permit_units` | us_fiscal_policy | tax_revenue_share | permit_units | - | 255 | 51 | 10.49 |
| `pcw100_us_fiscal_tax_revenue_share_hpi_growth` | us_fiscal_policy | tax_revenue_share | hpi_growth | + | 255 | 51 | 10.49 |
| `pcw100_us_fiscal_sales_tax_share_poverty` | us_fiscal_policy | sales_tax_share | poverty | + | 255 | 51 | 6.733 |
| `pcw100_us_fiscal_sales_tax_share_median_income` | us_fiscal_policy | sales_tax_share | median_income | - | 255 | 51 | 6.733 |
| `pcw100_us_fiscal_sales_tax_share_employment_ratio` | us_fiscal_policy | sales_tax_share | employment_ratio | - | 255 | 51 | 6.733 |
| `pcw100_us_fiscal_sales_tax_share_permit_units` | us_fiscal_policy | sales_tax_share | permit_units | - | 255 | 51 | 6.733 |
| `pcw100_us_fiscal_sales_tax_share_hpi_growth` | us_fiscal_policy | sales_tax_share | hpi_growth | - | 255 | 51 | 6.733 |
| `pcw100_us_fiscal_income_tax_share_poverty` | us_fiscal_policy | income_tax_share | poverty | - | 220 | 44 | 6.978 |
| `pcw100_us_fiscal_income_tax_share_median_income` | us_fiscal_policy | income_tax_share | median_income | + | 220 | 44 | 6.978 |
| `pcw100_us_fiscal_income_tax_share_employment_ratio` | us_fiscal_policy | income_tax_share | employment_ratio | - | 220 | 44 | 6.978 |
| `pcw100_us_fiscal_income_tax_share_permit_units` | us_fiscal_policy | income_tax_share | permit_units | - | 220 | 44 | 6.978 |
| `pcw100_us_fiscal_income_tax_share_hpi_growth` | us_fiscal_policy | income_tax_share | hpi_growth | - | 220 | 44 | 6.978 |
| `pcw100_us_fiscal_debt_revenue_ratio_poverty` | us_fiscal_policy | debt_revenue_ratio | poverty | + | 255 | 51 | 24.32 |
| `pcw100_us_fiscal_debt_revenue_ratio_median_income` | us_fiscal_policy | debt_revenue_ratio | median_income | - | 255 | 51 | 24.32 |
| `pcw100_us_fiscal_debt_revenue_ratio_employment_ratio` | us_fiscal_policy | debt_revenue_ratio | employment_ratio | - | 255 | 51 | 24.32 |
| `pcw100_us_fiscal_debt_revenue_ratio_permit_units` | us_fiscal_policy | debt_revenue_ratio | permit_units | - | 255 | 51 | 24.32 |
| `pcw100_us_fiscal_debt_revenue_ratio_hpi_growth` | us_fiscal_policy | debt_revenue_ratio | hpi_growth | - | 255 | 51 | 24.32 |
| `pcw100_global_efw_size_government_gdp_growth` | international_policy | size_government | gdp_growth | + | 163 | 163 | 1.42 |
| `pcw100_global_efw_size_government_employment` | international_policy | size_government | employment | + | 162 | 162 | 1.423 |
| `pcw100_global_efw_size_government_unemployment` | international_policy | size_government | unemployment | - | 162 | 162 | 1.423 |
| `pcw100_global_efw_size_government_investment` | international_policy | size_government | investment | + | 141 | 141 | 1.455 |
| `pcw100_global_efw_size_government_manufacturing` | international_policy | size_government | manufacturing | + | 147 | 147 | 1.429 |
| `pcw100_global_efw_size_government_fdi` | international_policy | size_government | fdi | + | 163 | 163 | 1.42 |
| `pcw100_global_efw_size_government_life_expectancy` | international_policy | size_government | life_expectancy | + | 163 | 163 | 1.42 |
| `pcw100_global_efw_size_government_under5_mortality` | international_policy | size_government | under5_mortality | - | 162 | 162 | 1.417 |
| `pcw100_global_efw_size_government_private_credit` | international_policy | size_government | private_credit | + | 115 | 115 | 1.496 |
| `pcw100_global_efw_size_government_hightech_exports` | international_policy | size_government | hightech_exports | + | 100 | 100 | 1.273 |
| `pcw100_global_efw_legal_rights_gdp_growth` | international_policy | legal_rights | gdp_growth | + | 163 | 163 | 2.464 |
| `pcw100_global_efw_legal_rights_employment` | international_policy | legal_rights | employment | + | 162 | 162 | 2.481 |
| `pcw100_global_efw_legal_rights_unemployment` | international_policy | legal_rights | unemployment | - | 162 | 162 | 2.481 |
| `pcw100_global_efw_legal_rights_investment` | international_policy | legal_rights | investment | + | 141 | 141 | 2.606 |
| `pcw100_global_efw_legal_rights_manufacturing` | international_policy | legal_rights | manufacturing | + | 147 | 147 | 2.205 |
| `pcw100_global_efw_legal_rights_fdi` | international_policy | legal_rights | fdi | + | 163 | 163 | 2.464 |
| `pcw100_global_efw_legal_rights_life_expectancy` | international_policy | legal_rights | life_expectancy | + | 163 | 163 | 2.464 |
| `pcw100_global_efw_legal_rights_under5_mortality` | international_policy | legal_rights | under5_mortality | - | 162 | 162 | 2.458 |
| `pcw100_global_efw_legal_rights_private_credit` | international_policy | legal_rights | private_credit | + | 115 | 115 | 2.32 |
| `pcw100_global_efw_legal_rights_hightech_exports` | international_policy | legal_rights | hightech_exports | + | 100 | 100 | 2.727 |
| `pcw100_global_efw_sound_money_gdp_growth` | international_policy | sound_money | gdp_growth | + | 163 | 163 | 2.153 |
| `pcw100_global_efw_sound_money_employment` | international_policy | sound_money | employment | + | 162 | 162 | 2.168 |
| `pcw100_global_efw_sound_money_unemployment` | international_policy | sound_money | unemployment | - | 162 | 162 | 2.168 |
| `pcw100_global_efw_sound_money_investment` | international_policy | sound_money | investment | + | 141 | 141 | 2.284 |
| `pcw100_global_efw_sound_money_manufacturing` | international_policy | sound_money | manufacturing | + | 147 | 147 | 2.182 |
| `pcw100_global_efw_sound_money_fdi` | international_policy | sound_money | fdi | + | 163 | 163 | 2.153 |
| `pcw100_global_efw_sound_money_life_expectancy` | international_policy | sound_money | life_expectancy | + | 163 | 163 | 2.153 |
| `pcw100_global_efw_sound_money_under5_mortality` | international_policy | sound_money | under5_mortality | - | 162 | 162 | 2.123 |
| `pcw100_global_efw_sound_money_private_credit` | international_policy | sound_money | private_credit | + | 115 | 115 | 2.084 |
| `pcw100_global_efw_sound_money_hightech_exports` | international_policy | sound_money | hightech_exports | + | 100 | 100 | 1.583 |
| `pcw100_global_efw_trade_freedom_gdp_growth` | international_policy | trade_freedom | gdp_growth | + | 163 | 163 | 1.892 |
| `pcw100_global_efw_trade_freedom_employment` | international_policy | trade_freedom | employment | + | 162 | 162 | 1.893 |
| `pcw100_global_efw_trade_freedom_unemployment` | international_policy | trade_freedom | unemployment | - | 162 | 162 | 1.893 |
| `pcw100_global_efw_trade_freedom_investment` | international_policy | trade_freedom | investment | + | 141 | 141 | 1.935 |
| `pcw100_global_efw_trade_freedom_manufacturing` | international_policy | trade_freedom | manufacturing | + | 147 | 147 | 1.792 |
| `pcw100_global_efw_trade_freedom_fdi` | international_policy | trade_freedom | fdi | + | 163 | 163 | 1.892 |
| `pcw100_global_efw_trade_freedom_life_expectancy` | international_policy | trade_freedom | life_expectancy | + | 163 | 163 | 1.892 |
| `pcw100_global_efw_trade_freedom_under5_mortality` | international_policy | trade_freedom | under5_mortality | - | 162 | 162 | 1.893 |
| `pcw100_global_efw_trade_freedom_private_credit` | international_policy | trade_freedom | private_credit | + | 115 | 115 | 1.896 |
| `pcw100_global_efw_trade_freedom_hightech_exports` | international_policy | trade_freedom | hightech_exports | + | 100 | 100 | 1.721 |
| `pcw100_global_efw_regulation_gdp_growth` | international_policy | regulation | gdp_growth | + | 163 | 163 | 1.48 |
| `pcw100_global_efw_regulation_employment` | international_policy | regulation | employment | + | 162 | 162 | 1.473 |
| `pcw100_global_efw_regulation_unemployment` | international_policy | regulation | unemployment | - | 162 | 162 | 1.473 |
| `pcw100_global_efw_regulation_investment` | international_policy | regulation | investment | + | 141 | 141 | 1.462 |
| `pcw100_global_efw_regulation_manufacturing` | international_policy | regulation | manufacturing | + | 147 | 147 | 1.387 |
| `pcw100_global_efw_regulation_fdi` | international_policy | regulation | fdi | + | 163 | 163 | 1.48 |
| `pcw100_global_efw_regulation_life_expectancy` | international_policy | regulation | life_expectancy | + | 163 | 163 | 1.48 |
| `pcw100_global_efw_regulation_under5_mortality` | international_policy | regulation | under5_mortality | - | 162 | 162 | 1.473 |
| `pcw100_global_efw_regulation_private_credit` | international_policy | regulation | private_credit | + | 115 | 115 | 1.255 |
| `pcw100_global_efw_regulation_hightech_exports` | international_policy | regulation | hightech_exports | + | 100 | 100 | 1.063 |
