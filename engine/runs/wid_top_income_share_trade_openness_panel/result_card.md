# Result card - wid_top_income_share_trade_openness_panel

**Verdict:** PARTIAL - coefficient is not statistically decisive at p<0.10.

## Plain-English Claim

Higher WDI trade openness should be positively associated with WID top 0.1 percent pre-tax income shares after country/year fixed effects and GDP, population, and regulatory-quality controls.

## Estimate

- Method: linearmodels.PanelOLS
- Coefficient on trade openness: **+0.0130**
- Clustered standard error: **0.0101**
- p-value: **0.1963**
- Observations: **975** country-years across **39** countries
- Within R-squared: **0.0736**
- Raw high-trade-quartile top-share contrast: **-2.1240 pp**

## Specification

`top_0_1_pretax_income_share ~ trade_open_gdp + log_gdp_pc_ppp + regulatory_quality + log_population + country_FE + year_FE`

The sample is 1996-2023 after the WGI join, with countries requiring at least 15 paired observations. This is an associational panel screen, not a causal trade-shock design. The raw quartile contrast is descriptive context only and is not used for the verdict.

## Data

Vintages and SHA-256 hashes are pinned in `manifest.yaml`; row-level panel data for visualization is in `chart_data.json`.
