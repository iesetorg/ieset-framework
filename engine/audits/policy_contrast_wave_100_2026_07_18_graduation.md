# Policy Contrast Wave 100 — graduation audit

- Hypotheses: 100
- Graduated: 100
- All graduated: **True**
- Verdicts: {"PARTIAL": 69, "REFUTED": 2, "SUPPORTED": 29}
- Cohorts: {"international_policy": 50, "us_fiscal_policy": 20, "us_minimum_wage": 30}

A hypothesis graduates only when its schema-valid preregistration and steelman exist, git history verifies strict preregistration, its registered data gate passes, its verdict is SUPPORTED/REFUTED/PARTIAL, every run artifact exists, and every input hash in the evidence packet matches.

## Results

| hypothesis | cohort | verdict | graduated |
| --- | --- | --- | :---: |
| `pcw100_us_mw_binding_premium_unemployment` | us_minimum_wage | PARTIAL | yes |
| `pcw100_us_mw_binding_premium_employment_ratio` | us_minimum_wage | PARTIAL | yes |
| `pcw100_us_mw_binding_premium_median_wage` | us_minimum_wage | PARTIAL | yes |
| `pcw100_us_mw_binding_premium_p10_wage` | us_minimum_wage | SUPPORTED | yes |
| `pcw100_us_mw_binding_premium_median_wage_growth` | us_minimum_wage | PARTIAL | yes |
| `pcw100_us_mw_binding_premium_food_employment_growth` | us_minimum_wage | PARTIAL | yes |
| `pcw100_us_mw_binding_premium_total_weekly_wage` | us_minimum_wage | PARTIAL | yes |
| `pcw100_us_mw_binding_premium_food_weekly_wage` | us_minimum_wage | SUPPORTED | yes |
| `pcw100_us_mw_binding_premium_food_establishment_growth` | us_minimum_wage | SUPPORTED | yes |
| `pcw100_us_mw_binding_premium_poverty` | us_minimum_wage | PARTIAL | yes |
| `pcw100_us_mw_bite_ratio_unemployment` | us_minimum_wage | PARTIAL | yes |
| `pcw100_us_mw_bite_ratio_employment_ratio` | us_minimum_wage | PARTIAL | yes |
| `pcw100_us_mw_bite_ratio_median_wage` | us_minimum_wage | PARTIAL | yes |
| `pcw100_us_mw_bite_ratio_p10_wage` | us_minimum_wage | SUPPORTED | yes |
| `pcw100_us_mw_bite_ratio_median_wage_growth` | us_minimum_wage | REFUTED | yes |
| `pcw100_us_mw_bite_ratio_food_employment_growth` | us_minimum_wage | PARTIAL | yes |
| `pcw100_us_mw_bite_ratio_total_weekly_wage` | us_minimum_wage | PARTIAL | yes |
| `pcw100_us_mw_bite_ratio_food_weekly_wage` | us_minimum_wage | SUPPORTED | yes |
| `pcw100_us_mw_bite_ratio_food_establishment_growth` | us_minimum_wage | PARTIAL | yes |
| `pcw100_us_mw_bite_ratio_poverty` | us_minimum_wage | PARTIAL | yes |
| `pcw100_us_mw_increase_event_unemployment` | us_minimum_wage | PARTIAL | yes |
| `pcw100_us_mw_increase_event_employment_ratio` | us_minimum_wage | PARTIAL | yes |
| `pcw100_us_mw_increase_event_median_wage` | us_minimum_wage | PARTIAL | yes |
| `pcw100_us_mw_increase_event_p10_wage` | us_minimum_wage | PARTIAL | yes |
| `pcw100_us_mw_increase_event_median_wage_growth` | us_minimum_wage | PARTIAL | yes |
| `pcw100_us_mw_increase_event_food_employment_growth` | us_minimum_wage | PARTIAL | yes |
| `pcw100_us_mw_increase_event_total_weekly_wage` | us_minimum_wage | PARTIAL | yes |
| `pcw100_us_mw_increase_event_food_weekly_wage` | us_minimum_wage | PARTIAL | yes |
| `pcw100_us_mw_increase_event_food_establishment_growth` | us_minimum_wage | PARTIAL | yes |
| `pcw100_us_mw_increase_event_poverty` | us_minimum_wage | PARTIAL | yes |
| `pcw100_us_fiscal_tax_revenue_share_poverty` | us_fiscal_policy | PARTIAL | yes |
| `pcw100_us_fiscal_tax_revenue_share_median_income` | us_fiscal_policy | PARTIAL | yes |
| `pcw100_us_fiscal_tax_revenue_share_employment_ratio` | us_fiscal_policy | SUPPORTED | yes |
| `pcw100_us_fiscal_tax_revenue_share_permit_units` | us_fiscal_policy | PARTIAL | yes |
| `pcw100_us_fiscal_tax_revenue_share_hpi_growth` | us_fiscal_policy | PARTIAL | yes |
| `pcw100_us_fiscal_sales_tax_share_poverty` | us_fiscal_policy | PARTIAL | yes |
| `pcw100_us_fiscal_sales_tax_share_median_income` | us_fiscal_policy | PARTIAL | yes |
| `pcw100_us_fiscal_sales_tax_share_employment_ratio` | us_fiscal_policy | PARTIAL | yes |
| `pcw100_us_fiscal_sales_tax_share_permit_units` | us_fiscal_policy | PARTIAL | yes |
| `pcw100_us_fiscal_sales_tax_share_hpi_growth` | us_fiscal_policy | PARTIAL | yes |
| `pcw100_us_fiscal_income_tax_share_poverty` | us_fiscal_policy | PARTIAL | yes |
| `pcw100_us_fiscal_income_tax_share_median_income` | us_fiscal_policy | PARTIAL | yes |
| `pcw100_us_fiscal_income_tax_share_employment_ratio` | us_fiscal_policy | PARTIAL | yes |
| `pcw100_us_fiscal_income_tax_share_permit_units` | us_fiscal_policy | PARTIAL | yes |
| `pcw100_us_fiscal_income_tax_share_hpi_growth` | us_fiscal_policy | PARTIAL | yes |
| `pcw100_us_fiscal_debt_revenue_ratio_poverty` | us_fiscal_policy | PARTIAL | yes |
| `pcw100_us_fiscal_debt_revenue_ratio_median_income` | us_fiscal_policy | PARTIAL | yes |
| `pcw100_us_fiscal_debt_revenue_ratio_employment_ratio` | us_fiscal_policy | PARTIAL | yes |
| `pcw100_us_fiscal_debt_revenue_ratio_permit_units` | us_fiscal_policy | PARTIAL | yes |
| `pcw100_us_fiscal_debt_revenue_ratio_hpi_growth` | us_fiscal_policy | PARTIAL | yes |
| `pcw100_global_efw_size_government_gdp_growth` | international_policy | PARTIAL | yes |
| `pcw100_global_efw_size_government_employment` | international_policy | SUPPORTED | yes |
| `pcw100_global_efw_size_government_unemployment` | international_policy | PARTIAL | yes |
| `pcw100_global_efw_size_government_investment` | international_policy | PARTIAL | yes |
| `pcw100_global_efw_size_government_manufacturing` | international_policy | PARTIAL | yes |
| `pcw100_global_efw_size_government_fdi` | international_policy | SUPPORTED | yes |
| `pcw100_global_efw_size_government_life_expectancy` | international_policy | PARTIAL | yes |
| `pcw100_global_efw_size_government_under5_mortality` | international_policy | PARTIAL | yes |
| `pcw100_global_efw_size_government_private_credit` | international_policy | PARTIAL | yes |
| `pcw100_global_efw_size_government_hightech_exports` | international_policy | PARTIAL | yes |
| `pcw100_global_efw_legal_rights_gdp_growth` | international_policy | SUPPORTED | yes |
| `pcw100_global_efw_legal_rights_employment` | international_policy | PARTIAL | yes |
| `pcw100_global_efw_legal_rights_unemployment` | international_policy | PARTIAL | yes |
| `pcw100_global_efw_legal_rights_investment` | international_policy | SUPPORTED | yes |
| `pcw100_global_efw_legal_rights_manufacturing` | international_policy | REFUTED | yes |
| `pcw100_global_efw_legal_rights_fdi` | international_policy | PARTIAL | yes |
| `pcw100_global_efw_legal_rights_life_expectancy` | international_policy | SUPPORTED | yes |
| `pcw100_global_efw_legal_rights_under5_mortality` | international_policy | SUPPORTED | yes |
| `pcw100_global_efw_legal_rights_private_credit` | international_policy | PARTIAL | yes |
| `pcw100_global_efw_legal_rights_hightech_exports` | international_policy | SUPPORTED | yes |
| `pcw100_global_efw_sound_money_gdp_growth` | international_policy | SUPPORTED | yes |
| `pcw100_global_efw_sound_money_employment` | international_policy | SUPPORTED | yes |
| `pcw100_global_efw_sound_money_unemployment` | international_policy | PARTIAL | yes |
| `pcw100_global_efw_sound_money_investment` | international_policy | SUPPORTED | yes |
| `pcw100_global_efw_sound_money_manufacturing` | international_policy | PARTIAL | yes |
| `pcw100_global_efw_sound_money_fdi` | international_policy | PARTIAL | yes |
| `pcw100_global_efw_sound_money_life_expectancy` | international_policy | PARTIAL | yes |
| `pcw100_global_efw_sound_money_under5_mortality` | international_policy | PARTIAL | yes |
| `pcw100_global_efw_sound_money_private_credit` | international_policy | SUPPORTED | yes |
| `pcw100_global_efw_sound_money_hightech_exports` | international_policy | PARTIAL | yes |
| `pcw100_global_efw_trade_freedom_gdp_growth` | international_policy | SUPPORTED | yes |
| `pcw100_global_efw_trade_freedom_employment` | international_policy | SUPPORTED | yes |
| `pcw100_global_efw_trade_freedom_unemployment` | international_policy | SUPPORTED | yes |
| `pcw100_global_efw_trade_freedom_investment` | international_policy | SUPPORTED | yes |
| `pcw100_global_efw_trade_freedom_manufacturing` | international_policy | PARTIAL | yes |
| `pcw100_global_efw_trade_freedom_fdi` | international_policy | SUPPORTED | yes |
| `pcw100_global_efw_trade_freedom_life_expectancy` | international_policy | SUPPORTED | yes |
| `pcw100_global_efw_trade_freedom_under5_mortality` | international_policy | PARTIAL | yes |
| `pcw100_global_efw_trade_freedom_private_credit` | international_policy | PARTIAL | yes |
| `pcw100_global_efw_trade_freedom_hightech_exports` | international_policy | SUPPORTED | yes |
| `pcw100_global_efw_regulation_gdp_growth` | international_policy | SUPPORTED | yes |
| `pcw100_global_efw_regulation_employment` | international_policy | SUPPORTED | yes |
| `pcw100_global_efw_regulation_unemployment` | international_policy | PARTIAL | yes |
| `pcw100_global_efw_regulation_investment` | international_policy | SUPPORTED | yes |
| `pcw100_global_efw_regulation_manufacturing` | international_policy | PARTIAL | yes |
| `pcw100_global_efw_regulation_fdi` | international_policy | PARTIAL | yes |
| `pcw100_global_efw_regulation_life_expectancy` | international_policy | SUPPORTED | yes |
| `pcw100_global_efw_regulation_under5_mortality` | international_policy | PARTIAL | yes |
| `pcw100_global_efw_regulation_private_credit` | international_policy | SUPPORTED | yes |
| `pcw100_global_efw_regulation_hightech_exports` | international_policy | PARTIAL | yes |
