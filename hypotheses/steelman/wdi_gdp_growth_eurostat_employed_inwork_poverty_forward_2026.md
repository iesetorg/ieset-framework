# Steelman: real growth and in-work poverty among employed persons

## Fixed measured prediction

For the frozen 30-country roster, a one-percentage-point higher WDI real GDP
growth rate in calendar year `t` predicts at least a 0.1-percentage-point
smaller change in the Eurostat EU-SILC in-work at-risk-of-poverty rate for all
employed people aged 18–64 between survey years `t+1` and `t+2`. The sign,
practical size, 99.5% interval, and two-sided `p≤0.005` threshold are fixed
before the selected Eurostat outcomes are read. A plausible channel is that
real activity raises work hours or earnings and lowers poverty risk for some
employed households.

## Strongest rival account

EU-SILC poverty is relative to 60% of each country's median equivalised
disposable household income after transfers. Broadly shared income growth
can leave the relative poverty rate unchanged. GDP growth can come from
profits, productivity, or sectors that do not help low-income workers; wages,
hours, household composition, tax-transfer rules, inflation, and migration
can move the rate independently. The same macro shock can affect both GDP and
poverty. Two-way fixed effects remove stable country differences and common
years, not country-specific demand or policy shocks. The exposure can affect
the baseline income year, so this is a prospective descriptive association,
not an identified lagged causal effect.

The selected Eurostat parquet contains no observation-status or break-flag
column. The frozen rule is to use exact selector keys and, only after the
separate source lock, drop nonfinite or out-of-range endpoint rates; there is
no post-hoc flag-based or visual-break trimming. No claim that individual
country-years are break-free is warranted. The United Kingdom and Ireland
are excluded because their historical EU-SILC income reference conventions
departed from the prior-calendar-year convention.

## Prior IESET work and credit

Existing growth-poverty and in-work-benefit cases, including
`redistribution_market_income_growth_poverty_exit_panel`,
`bargaining_coverage_low_wage_poverty_employment_panel`, and
`eurozone_austerity_distributional_incidence`, make this question related to
the archive. A direct exact-source/phrase screen found no prior GDP-growth
to Eurostat `ilc_iw01` EMP `t+1→t+2` test. The EMP outcome contains some
people in the companion SAL outcome; the two fixed tests receive local
Bonferroni correction, with no claim of archive-wide independence.

All verdicts are reportable. Any support is descriptive calibration only;
there is zero causal, policy, school-score, and featured credit.

Sources: [WDI real GDP growth](https://data.worldbank.org/indicator/NY.GDP.MKTP.KD.ZG),
[Eurostat in-work poverty](https://ec.europa.eu/eurostat/databrowser/product/page/ILC_IW01),
[EU-SILC reference-year metadata](https://ec.europa.eu/eurostat/cache/metadata/en/ilc_sieusilc.htm).
