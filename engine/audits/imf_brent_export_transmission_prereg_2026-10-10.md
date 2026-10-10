# IMF Brent shocks, fixed fuel-export orientation and later macro responses — prospective registration

The single four-cell family asks whether countries whose merchandise exports were more fuel oriented in 2000-2004 have larger later macro responses to a common Brent price increase. The four distinct responses are current-account balance, fixed-investment share, real GDP per person and real private consumption per person. The IMF PCPS monthly Brent price and WDI merchandise fuel-export share measure an interaction proxy, not country-specific net oil trade or a policy. Prior IMF inflation→macro, WDI resource-rent→sector-growth and energy-price→industrial outcomes are different directed questions and are not independent confirmations.

## Value-blind source-key freeze

Shock years are 2005–2017; baseline fuel-export-share keys are 2000–2004; response endpoints end by 2019. The roster has 11,180 cell-specific structural keys. WDI files contain broad country×year grids even where values are null, so key counts are upper bounds only. Before this registration no selected numeric value or null mask, shock, baseline share, outcome change, sign or estimate was opened. This plan, four specs and steelmen, runner and key roster are one first-add commit. Four separate one-file source-lock commits must follow before any selected value access.

| Outcome | Source-key rows / countries | Registered sign | Meaningful beta per +1 interaction SD |
| --- | ---: | --- | --- |
| Current-account balance, percent of GDP | 2795 / 215 | positive | 0.5 percentage points |
| Gross fixed capital formation, percent of GDP | 2795 / 215 | positive | 0.4 percentage points |
| Real GDP per person | 2795 / 215 | positive | 0.015 log points |
| Real household consumption per person | 2795 / 215 | positive | 0.015 log points |

## Frozen measurement and failures

Fixed exposure is the 2000–2004 arithmetic mean of at least three valid national fuel-export shares [0,100], divided by 100, multiplied by log of annual-average Brent price in shock year t over t−1. Exactly twelve positive finite monthly prices are required for each annual average. Standardize the interaction using the pooled complete-case population SD separately per endpoint; +1 beta unit is +1 SD. Outcome is t→t+2 change in percentage points for current-account and investment shares, or log growth for income and private consumption. Control the same outcome’s t−2→t change, baseline level, baseline log real GDP per person except where it duplicates the income outcome, plus country and shock-year effects. Keep countries with at least five complete rows. Two-way country/year clustered CR1 SE; two-sided t with min(country,year clusters)−1 df; 99% descriptive intervals.

Each endpoint requires at least 500 rows, 50 countries and 10 shock years; at least 15 countries and 80 rows must have baseline fuel share ≥30%. Residualized standardized exposure SD ≥0.15; residualized outcome SD ≥0.25 percentage points for current-account and investment changes or ≥0.005 log points for real income and consumption growth. Top 1% row shares of squared residual exposure and outcome ≤0.3/0.3; maximum country shares ≤0.18/0.18; maximum shock-year shares ≤0.35/0.35. Five SHA256(country) mod 5 omissions require ≥350 rows and ≥35 countries each; four of five same-sign slopes. Rank or two-way cluster uncertainty failure is INCONCLUSIVE. Holm α=0.05 includes all four cells, with invalid cells p=1. Opposite signed material and Holm-significant result is REFUTED; method-valid but threshold-missing is PARTIAL. No post-result substitutions.

## Source custody, rights, limitations

All six raw source parquets and their exact tracked fetch-manifest entries are SHA-256 pinned. The IMF source manifest identifies POILBRE as Dated Brent, light blend, USD per barrel, monthly global W00; it records IMF attribution-required permissions. IMF published data terms permit attributed derived use and warn that some statistical products include third-party inputs. WDI records CC BY 4.0. This packet retains only derived diagnostics, not raw series rows. Source definitions: https://www.imf.org/en/research/commodity-prices ; https://www.imf.org/en/about/copyright-and-terms ; https://data.worldbank.org/indicator/TX.VAL.FUEL.ZS.UN .
The interaction does not measure import dependence or country-specific export receipts. Global demand, domestic extraction, exchange rates, fiscal policy and revisions can drive both exposure and outcomes. Two-way clustering helps with shared years but only thirteen shock years exist; no causal, policy, school, position or featured credit can follow. Holm is local to the selected family, not archive-wide correction.
