# Market-Order Follow-Up Results - 2026-05-03

## Methodology Gate

- Pre-registration commit: `10b90c446e93182c7b6104262d5b926fe09753b6`
- Estimation was run only after the 20 specs, steelmen, and reciprocal position links were committed.
- Each run directory includes `diagnostics.json`, `result_card.md`, and `replication.py`.
- Coverage flag: `thin_country_panel` means fewer than 10 countries; retain the verdict but review before strong scoreboard interpretation.

## Counts

- SUPPORTED: 7
- REFUTED: 2
- PARTIAL: 11

## FDR q<=0.10

- SUPPORTED: 6

## Coverage-Qualified FDR q<=0.10

- SUPPORTED: 5

## Thin Country Panels

- `market_order_government_effectiveness_private_investment_share_panel`
- `market_order_capital_account_openness_private_investment_share_panel`
- `market_order_fiscal_balance_private_investment_share_panel`
- `market_order_public_debt_private_investment_share_panel`
- `market_order_government_consumption_private_investment_share_panel`

## Results

- `market_order_government_effectiveness_private_investment_share_panel`: PARTIAL | coef=+1.875 | p=0.4071 | q=0.5429 | n=115 | countries=5; thin-country
- `market_order_government_effectiveness_gross_savings_share_panel`: PARTIAL | coef=+1.21 | p=0.1765 | q=0.3173 | n=741 | countries=33
- `market_order_government_effectiveness_manufacturing_share_panel`: PARTIAL | coef=+0.4806 | p=0.5972 | q=0.7026 | n=757 | countries=33
- `market_order_government_effectiveness_gdp_pc_growth_panel`: PARTIAL | coef=+0.4347 | p=0.4566 | q=0.5708 | n=759 | countries=33
- `market_order_capital_account_openness_fdi_inflows_share_panel`: PARTIAL | coef=-1.009 | p=0.6976 | q=0.7752 | n=858 | countries=33
- `market_order_capital_account_openness_private_investment_share_panel`: REFUTED | coef=-3.047 | p=0.09888 | q=0.2197 | n=130 | countries=5; thin-country
- `market_order_capital_account_openness_high_tech_exports_panel`: PARTIAL | coef=+2.548 | p=0.2221 | q=0.3173 | n=494 | countries=33
- `market_order_capital_account_openness_gdp_pc_growth_panel`: SUPPORTED | coef=+1.907 | p=0.01995 | q=0.06651 | n=858 | countries=33; FDR q<=0.10; coverage-qualified
- `market_order_fiscal_balance_private_investment_share_panel`: SUPPORTED | coef=+0.2315 | p=0.07779 | q=0.1969 | n=122 | countries=5; thin-country
- `market_order_fiscal_balance_gross_savings_share_panel`: SUPPORTED | coef=+0.3266 | p=0.001431 | q=0.007157 | n=787 | countries=32; FDR q<=0.10; coverage-qualified
- `market_order_fiscal_balance_gdp_pc_growth_panel`: SUPPORTED | coef=+0.1811 | p=0.0002113 | q=0.001408 | n=812 | countries=32; FDR q<=0.10; coverage-qualified
- `market_order_fiscal_balance_private_credit_depth_panel`: REFUTED | coef=-1.028 | p=0.07878 | q=0.1969 | n=668 | countries=32
- `market_order_public_debt_private_investment_share_panel`: SUPPORTED | coef=-0.1888 | p=0.008425 | q=0.0337 | n=51 | countries=4; FDR q<=0.10; thin-country
- `market_order_public_debt_gross_savings_share_panel`: PARTIAL | coef=+0.005145 | p=0.8306 | q=0.8743 | n=231 | countries=12
- `market_order_public_debt_gdp_pc_growth_panel`: PARTIAL | coef=-0.0007575 | p=0.9188 | q=0.9188 | n=231 | countries=12
- `market_order_public_debt_private_credit_depth_panel`: PARTIAL | coef=-0.2819 | p=0.1826 | q=0.3173 | n=190 | countries=11
- `market_order_government_consumption_private_investment_share_panel`: PARTIAL | coef=-0.2076 | p=0.2167 | q=0.3173 | n=130 | countries=5; thin-country
- `market_order_government_consumption_gross_savings_share_panel`: SUPPORTED | coef=-1.063 | p=1.25e-07 | q=2.5e-06 | n=829 | countries=33; FDR q<=0.10; coverage-qualified
- `market_order_government_consumption_manufacturing_share_panel`: PARTIAL | coef=-0.2202 | p=0.2129 | q=0.3173 | n=856 | countries=33
- `market_order_government_consumption_gdp_pc_growth_panel`: SUPPORTED | coef=-0.4576 | p=0.0001629 | q=0.001408 | n=858 | countries=33; FDR q<=0.10; coverage-qualified
