# Steelman: real growth and in-work poverty among employees

## Fixed measured prediction

For the frozen 30-country roster, a one-percentage-point higher WDI real GDP
growth rate in calendar year `t` predicts at least a 0.1-percentage-point
smaller change in the Eurostat EU-SILC in-work at-risk-of-poverty rate for
employees aged 18–64 between survey years `t+1` and `t+2`. The sign,
practical size, 99.5% interval, and two-sided `p≤0.005` threshold are fixed
before the selected Eurostat outcomes are read. The strongest mechanism is
growth in employee hours or wages among low-income households.

## Strongest rival account

Relative poverty can stay flat while employee incomes rise. Employment
composition, bargaining, wage floors, tax-transfer policy, household size,
and the median income threshold can change together with GDP growth. Annual
GDP growth does not isolate a policy or exogenous shock. The survey-year
income lag gives a chronological prediction, but the treatment can affect
the baseline reference income year. The endpoint difference can therefore
reflect regression to the mean or unmeasured common forces. Fixed effects
do not remove these threats.

The pinned Eurostat parquet has no observation-status or break flag. Exact
selector keys are frozen; after the separate source lock, nonfinite and
out-of-[0,100] endpoint values are excluded. No result may be described as
break-screened, and no ad hoc country-year or outcome-magnitude trimming is
allowed. The United Kingdom and Ireland are excluded for historical
EU-SILC income reference-year exceptions.

## Prior IESET work and credit

`bargaining_coverage_low_wage_poverty_employment_panel` discusses in-work
poverty with bargaining exposure. `welfare_transfer_france_rsa_prime_dactivite_employment_effect`
and `eurozone_austerity_distributional_incidence` also mention Eurostat
`ilc_iw01`, under different intervention designs. A direct exact-source/phrase
screen found no prior GDP-growth to `ilc_iw01` SAL `t+1→t+2` test. SAL is
nested within the companion EMP population, so the two outcomes are
correlated; Bonferroni correction covers this fixed local family only.

All verdicts are reportable. Any support is descriptive calibration only;
there is zero causal, policy, school-score, and featured credit.

Sources: [WDI real GDP growth](https://data.worldbank.org/indicator/NY.GDP.MKTP.KD.ZG),
[Eurostat in-work poverty](https://ec.europa.eu/eurostat/databrowser/product/page/ILC_IW01),
[EU-SILC reference-year metadata](https://ec.europa.eu/eurostat/cache/metadata/en/ilc_sieusilc.htm).
