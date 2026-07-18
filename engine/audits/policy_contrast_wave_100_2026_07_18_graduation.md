# Policy Contrast Wave 100 — graduation audit

- Hypotheses: 100
- Graduated: 100
- All graduated: **True**
- Verdicts: {"PARTIAL": 69, "REFUTED": 2, "SUPPORTED": 29}
- Cohorts: {"international_policy": 50, "us_fiscal_policy": 20, "us_minimum_wage": 30}
- Benjamini-Hochberg q<0.10 signals: 17 (16 supported, 1 refuted)

A hypothesis graduates only when its schema-valid preregistration and steelman exist, git history verifies strict preregistration, its registered data gate passes, its verdict is SUPPORTED/REFUTED/PARTIAL, every run artifact exists, and every input hash in the evidence packet matches.

## Results

| hypothesis | cohort | verdict | BH q-value | graduated |
| --- | --- | --- | ---: | :---: |
| `pcw100_us_mw_binding_premium_unemployment` | us_minimum_wage | PARTIAL | 0.8812 | yes |
| `pcw100_us_mw_binding_premium_employment_ratio` | us_minimum_wage | PARTIAL | 0.488 | yes |
| `pcw100_us_mw_binding_premium_median_wage` | us_minimum_wage | PARTIAL | 0.4833 | yes |
| `pcw100_us_mw_binding_premium_p10_wage` | us_minimum_wage | SUPPORTED | 3.714e-11 | yes |
| `pcw100_us_mw_binding_premium_median_wage_growth` | us_minimum_wage | PARTIAL | 0.9365 | yes |
| `pcw100_us_mw_binding_premium_food_employment_growth` | us_minimum_wage | PARTIAL | 0.4833 | yes |
| `pcw100_us_mw_binding_premium_total_weekly_wage` | us_minimum_wage | PARTIAL | 0.7205 | yes |
| `pcw100_us_mw_binding_premium_food_weekly_wage` | us_minimum_wage | SUPPORTED | 2.341e-05 | yes |
| `pcw100_us_mw_binding_premium_food_establishment_growth` | us_minimum_wage | SUPPORTED | 0.3089 | yes |
| `pcw100_us_mw_binding_premium_poverty` | us_minimum_wage | PARTIAL | 0.6641 | yes |
| `pcw100_us_mw_bite_ratio_unemployment` | us_minimum_wage | PARTIAL | 0.6306 | yes |
| `pcw100_us_mw_bite_ratio_employment_ratio` | us_minimum_wage | PARTIAL | 0.9027 | yes |
| `pcw100_us_mw_bite_ratio_median_wage` | us_minimum_wage | PARTIAL | 0.4836 | yes |
| `pcw100_us_mw_bite_ratio_p10_wage` | us_minimum_wage | SUPPORTED | 4.048e-10 | yes |
| `pcw100_us_mw_bite_ratio_median_wage_growth` | us_minimum_wage | REFUTED | 0.1473 | yes |
| `pcw100_us_mw_bite_ratio_food_employment_growth` | us_minimum_wage | PARTIAL | 0.4833 | yes |
| `pcw100_us_mw_bite_ratio_total_weekly_wage` | us_minimum_wage | PARTIAL | 0.6421 | yes |
| `pcw100_us_mw_bite_ratio_food_weekly_wage` | us_minimum_wage | SUPPORTED | 0.0001211 | yes |
| `pcw100_us_mw_bite_ratio_food_establishment_growth` | us_minimum_wage | PARTIAL | 0.4836 | yes |
| `pcw100_us_mw_bite_ratio_poverty` | us_minimum_wage | PARTIAL | 0.6641 | yes |
| `pcw100_us_mw_increase_event_unemployment` | us_minimum_wage | PARTIAL | 0.8727 | yes |
| `pcw100_us_mw_increase_event_employment_ratio` | us_minimum_wage | PARTIAL | 0.9394 | yes |
| `pcw100_us_mw_increase_event_median_wage` | us_minimum_wage | PARTIAL | 0.6641 | yes |
| `pcw100_us_mw_increase_event_p10_wage` | us_minimum_wage | PARTIAL | 0.4836 | yes |
| `pcw100_us_mw_increase_event_median_wage_growth` | us_minimum_wage | PARTIAL | 0.7886 | yes |
| `pcw100_us_mw_increase_event_food_employment_growth` | us_minimum_wage | PARTIAL | 0.4427 | yes |
| `pcw100_us_mw_increase_event_total_weekly_wage` | us_minimum_wage | PARTIAL | 0.6597 | yes |
| `pcw100_us_mw_increase_event_food_weekly_wage` | us_minimum_wage | PARTIAL | 0.4836 | yes |
| `pcw100_us_mw_increase_event_food_establishment_growth` | us_minimum_wage | PARTIAL | 0.4836 | yes |
| `pcw100_us_mw_increase_event_poverty` | us_minimum_wage | PARTIAL | 0.5238 | yes |
| `pcw100_us_fiscal_tax_revenue_share_poverty` | us_fiscal_policy | PARTIAL | 0.8383 | yes |
| `pcw100_us_fiscal_tax_revenue_share_median_income` | us_fiscal_policy | PARTIAL | 0.8727 | yes |
| `pcw100_us_fiscal_tax_revenue_share_employment_ratio` | us_fiscal_policy | SUPPORTED | 0.2662 | yes |
| `pcw100_us_fiscal_tax_revenue_share_permit_units` | us_fiscal_policy | PARTIAL | 0.6641 | yes |
| `pcw100_us_fiscal_tax_revenue_share_hpi_growth` | us_fiscal_policy | PARTIAL | 0.7498 | yes |
| `pcw100_us_fiscal_sales_tax_share_poverty` | us_fiscal_policy | PARTIAL | 0.6641 | yes |
| `pcw100_us_fiscal_sales_tax_share_median_income` | us_fiscal_policy | PARTIAL | 0.8727 | yes |
| `pcw100_us_fiscal_sales_tax_share_employment_ratio` | us_fiscal_policy | PARTIAL | 0.6528 | yes |
| `pcw100_us_fiscal_sales_tax_share_permit_units` | us_fiscal_policy | PARTIAL | 0.6306 | yes |
| `pcw100_us_fiscal_sales_tax_share_hpi_growth` | us_fiscal_policy | PARTIAL | 0.4833 | yes |
| `pcw100_us_fiscal_income_tax_share_poverty` | us_fiscal_policy | PARTIAL | 0.9394 | yes |
| `pcw100_us_fiscal_income_tax_share_median_income` | us_fiscal_policy | PARTIAL | 0.7333 | yes |
| `pcw100_us_fiscal_income_tax_share_employment_ratio` | us_fiscal_policy | PARTIAL | 0.7498 | yes |
| `pcw100_us_fiscal_income_tax_share_permit_units` | us_fiscal_policy | PARTIAL | 0.5315 | yes |
| `pcw100_us_fiscal_income_tax_share_hpi_growth` | us_fiscal_policy | PARTIAL | 0.6242 | yes |
| `pcw100_us_fiscal_debt_revenue_ratio_poverty` | us_fiscal_policy | PARTIAL | 0.8642 | yes |
| `pcw100_us_fiscal_debt_revenue_ratio_median_income` | us_fiscal_policy | PARTIAL | 0.9862 | yes |
| `pcw100_us_fiscal_debt_revenue_ratio_employment_ratio` | us_fiscal_policy | PARTIAL | 0.7209 | yes |
| `pcw100_us_fiscal_debt_revenue_ratio_permit_units` | us_fiscal_policy | PARTIAL | 0.7506 | yes |
| `pcw100_us_fiscal_debt_revenue_ratio_hpi_growth` | us_fiscal_policy | PARTIAL | 0.8314 | yes |
| `pcw100_global_efw_size_government_gdp_growth` | international_policy | PARTIAL | 0.6641 | yes |
| `pcw100_global_efw_size_government_employment` | international_policy | SUPPORTED | 0.2428 | yes |
| `pcw100_global_efw_size_government_unemployment` | international_policy | PARTIAL | 0.4589 | yes |
| `pcw100_global_efw_size_government_investment` | international_policy | PARTIAL | 0.7498 | yes |
| `pcw100_global_efw_size_government_manufacturing` | international_policy | PARTIAL | 0.9373 | yes |
| `pcw100_global_efw_size_government_fdi` | international_policy | SUPPORTED | 0.2292 | yes |
| `pcw100_global_efw_size_government_life_expectancy` | international_policy | PARTIAL | 0.3089 | yes |
| `pcw100_global_efw_size_government_under5_mortality` | international_policy | PARTIAL | 0.8383 | yes |
| `pcw100_global_efw_size_government_private_credit` | international_policy | PARTIAL | 0.4589 | yes |
| `pcw100_global_efw_size_government_hightech_exports` | international_policy | PARTIAL | 0.6528 | yes |
| `pcw100_global_efw_legal_rights_gdp_growth` | international_policy | SUPPORTED | 0.005521 | yes |
| `pcw100_global_efw_legal_rights_employment` | international_policy | PARTIAL | 0.6306 | yes |
| `pcw100_global_efw_legal_rights_unemployment` | international_policy | PARTIAL | 0.3089 | yes |
| `pcw100_global_efw_legal_rights_investment` | international_policy | SUPPORTED | 0.001447 | yes |
| `pcw100_global_efw_legal_rights_manufacturing` | international_policy | REFUTED | 0.04851 | yes |
| `pcw100_global_efw_legal_rights_fdi` | international_policy | PARTIAL | 0.4821 | yes |
| `pcw100_global_efw_legal_rights_life_expectancy` | international_policy | SUPPORTED | 0.000198 | yes |
| `pcw100_global_efw_legal_rights_under5_mortality` | international_policy | SUPPORTED | 0.06683 | yes |
| `pcw100_global_efw_legal_rights_private_credit` | international_policy | PARTIAL | 0.6306 | yes |
| `pcw100_global_efw_legal_rights_hightech_exports` | international_policy | SUPPORTED | 0.2662 | yes |
| `pcw100_global_efw_sound_money_gdp_growth` | international_policy | SUPPORTED | 0.09753 | yes |
| `pcw100_global_efw_sound_money_employment` | international_policy | SUPPORTED | 0.005521 | yes |
| `pcw100_global_efw_sound_money_unemployment` | international_policy | PARTIAL | 0.6641 | yes |
| `pcw100_global_efw_sound_money_investment` | international_policy | SUPPORTED | 0.001067 | yes |
| `pcw100_global_efw_sound_money_manufacturing` | international_policy | PARTIAL | 0.4479 | yes |
| `pcw100_global_efw_sound_money_fdi` | international_policy | PARTIAL | 0.3112 | yes |
| `pcw100_global_efw_sound_money_life_expectancy` | international_policy | PARTIAL | 0.6641 | yes |
| `pcw100_global_efw_sound_money_under5_mortality` | international_policy | PARTIAL | 0.6528 | yes |
| `pcw100_global_efw_sound_money_private_credit` | international_policy | SUPPORTED | 0.2428 | yes |
| `pcw100_global_efw_sound_money_hightech_exports` | international_policy | PARTIAL | 0.6306 | yes |
| `pcw100_global_efw_trade_freedom_gdp_growth` | international_policy | SUPPORTED | 0.01249 | yes |
| `pcw100_global_efw_trade_freedom_employment` | international_policy | SUPPORTED | 0.0001324 | yes |
| `pcw100_global_efw_trade_freedom_unemployment` | international_policy | SUPPORTED | 0.1473 | yes |
| `pcw100_global_efw_trade_freedom_investment` | international_policy | SUPPORTED | 0.2292 | yes |
| `pcw100_global_efw_trade_freedom_manufacturing` | international_policy | PARTIAL | 0.3112 | yes |
| `pcw100_global_efw_trade_freedom_fdi` | international_policy | SUPPORTED | 0.2428 | yes |
| `pcw100_global_efw_trade_freedom_life_expectancy` | international_policy | SUPPORTED | 0.2292 | yes |
| `pcw100_global_efw_trade_freedom_under5_mortality` | international_policy | PARTIAL | 0.313 | yes |
| `pcw100_global_efw_trade_freedom_private_credit` | international_policy | PARTIAL | 0.6306 | yes |
| `pcw100_global_efw_trade_freedom_hightech_exports` | international_policy | SUPPORTED | 0.2428 | yes |
| `pcw100_global_efw_regulation_gdp_growth` | international_policy | SUPPORTED | 0.0002798 | yes |
| `pcw100_global_efw_regulation_employment` | international_policy | SUPPORTED | 0.08138 | yes |
| `pcw100_global_efw_regulation_unemployment` | international_policy | PARTIAL | 0.3479 | yes |
| `pcw100_global_efw_regulation_investment` | international_policy | SUPPORTED | 0.01399 | yes |
| `pcw100_global_efw_regulation_manufacturing` | international_policy | PARTIAL | 0.4589 | yes |
| `pcw100_global_efw_regulation_fdi` | international_policy | PARTIAL | 0.6528 | yes |
| `pcw100_global_efw_regulation_life_expectancy` | international_policy | SUPPORTED | 0.2428 | yes |
| `pcw100_global_efw_regulation_under5_mortality` | international_policy | PARTIAL | 0.3112 | yes |
| `pcw100_global_efw_regulation_private_credit` | international_policy | SUPPORTED | 0.2292 | yes |
| `pcw100_global_efw_regulation_hightech_exports` | international_policy | PARTIAL | 0.3763 | yes |
