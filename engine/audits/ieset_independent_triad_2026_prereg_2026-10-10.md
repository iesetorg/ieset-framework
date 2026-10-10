# Three distinct measured outcomes — frozen family preregistration

This is one prospectively selected **descriptive** three-test family. Its
outcomes are WHO all-residence ambient PM2.5, ILO female prime-age
labour-force participation, and WHO all-age suicide mortality. They are
different constructs and source tables, not three replications of one
effect. Each test retains its own ID, fixed key-only country roster,
exposure, controls, value validity rules, and falsification gates. All
three count in the family denominator, including INCONCLUSIVE results.

## Pre-value knowledge and source custody

Before this registration, only source bytes/hashes, fetch manifests,
schemas, official indicator definitions, selected dimension/year keys,
and key-only national-area rosters were inspected. No selected numeric
values, null masks, derived exposures/outcomes, model fits, or country
rankings were opened. National-area keys use ISO 3166 alpha-3 countries
or territories recognized by the fixed parser; non-country aggregates,
blank WDI geography, and unmatched WHO/ILO dimensions are excluded.
Key presence does not imply measured completeness.

| Role | Frozen raw vintage SHA-256 | Manifest SHA-256 |
| --- | --- | --- |
| IRENA installed_capacity_solar_pv 2026-05-05T212314Z | 5473eb1f2a057b831796c2c9394394c145c8ac14f74511841e8d4aeb74ddd205 | d09b3816f3aee52ff2dfd7849289cde9b027ac9b72669c741423b3d7db209718 |
| WDI SP.POP.TOTL 2026-05-05T194826Z | 6e8ccda8b27d188d08e0fbf036828c975641453c12e6e68d5807657140cd9456 | a571d660fd359d245176b77e595b59923a90a1e40a799ea56c13f001a7b09945 |
| WHO SDGPM25 2026-04-30T114744Z | c2cf89f4ab41dc8c4b6b251e7b47651edcd07d826cb45a7d5e1d8ab0ee4c6e34 | e4eba4196e874aa69112f5e93420aa1daeffe64225e73ff536b336e33dec282e |
| WDI SE.XPD.TOTL.GD.ZS 2026-05-05T204028Z | 0f21a848f064c16fce431b5425f5fb51519044c3e88256f329821b00504cc501 | 5022cf82e5656d89c54d3c0df1cc3c12718b93896488eebfde3ffa197beef112 |
| ILO EAP_2WAP_SEX_AGE_RT_A 2026-07-23T152621Z | 17e1ed07bf963364d866304ff6384dbbfb8bc06d5ba30b42a474098c2c54e395 | 367fc796f8738908e3be217054f798e7684d29acee3d7304107136aecd05cdb6 |
| WDI FP.CPI.TOTL.ZG 2026-05-05T194737Z | dd4c747352eb0ceab2600a6b6ffeeda048c6080f0097bb6927d9966e5a3242a0 | a571d660fd359d245176b77e595b59923a90a1e40a799ea56c13f001a7b09945 |
| WHO SDGSUICIDE 2026-04-30T114842Z | 72bf65650b553ac47df60cd624f21ad5d12c062694b3564ebbe300275ccec937 | e4eba4196e874aa69112f5e93420aa1daeffe64225e73ff536b336e33dec282e |

IRENA's fetch manifest records its license as unknown. WHO's manifests
record CC-BY-NC-SA-3.0 IGO; WDI and ILO record CC BY 4.0. Raw rows
remain in the read-only source checkout and are not copied into tracked
artifacts. The result includes source identities, model diagnostics,
aggregate coefficients where gates allow them, and empty chart arrays.

## Test 1: solar capacity and ambient PM2.5

The fixed roster has **140** national areas with exact IRENA solar-PV MW
and WDI population keys in 2010 and 2015 and WHO SDGPM25
SpatialDimType=COUNTRY, Dim1=RESIDENCEAREATYPE_TOTL keys in 2010, 2015,
and 2019. Roster SHA-256:
ec601ededde0590ad2603dcdbb824626aab1ab0c81d005ba2668a7267a961107.

Require finite nonnegative solar MW, positive population, and PM2.5 in
[0,500] micrograms per cubic metre at every endpoint. Solar intensity
is MW per million residents. Exposure X is log1p(intensity_2015) minus
log1p(intensity_2010). Outcome Y is PM2.5_2019 minus PM2.5_2015.
Controls are log1p(solar intensity_2010), PM2.5_2015, and the
2010–2015 PM2.5 change. A negative beta is the claimed direction.
This WHO total-residence slice is not the urban-only SDG summary.

## Test 2: education spending and female prime-age participation

The fixed roster has **183** national areas with WDI public education
expenditure/GDP keys in 2005 and 2015 and ILO
EAP_2WAP_SEX_AGE_RT_A, sex=SEX_F,
classif1=AGE_AGGREGATE_Y25-54 keys in 2005, 2015, and 2023.
Roster SHA-256:
3d6430fc9cf9e5d7016db12afc962f2dd13dd57ec8494d06608229c612a251f1.

Require finite spending share in [0,20] percent of GDP and finite
female participation in [0,100] percent at every endpoint. Exposure X
is spending share_2015 minus spending share_2005 in GDP percentage
points. Outcome Y is participation_2023 minus participation_2015 in
percentage points. Controls are spending share_2005, participation_2015,
and participation_2015 minus participation_2005. A positive beta is the
claimed direction. Spending is for all education, not women-specific
programmes; participation includes job seekers and may be modelled.

## Test 3: inflation volatility and suicide mortality

The fixed roster has **185** national areas with every annual WDI CPI
inflation key in 2005–2013 and WHO SDGSUICIDE
SpatialDimType=COUNTRY, Dim1=SEX_BTSX,
Dim2=AGEGROUP_YEARSALL keys in 2014 and 2021. Roster SHA-256:
153a79fc73ea16c106bc669723e5d74ac60051f02748e8ccbfcec8ec2b556bc6.

Require all nine CPI annual inflation rates finite in [-100,10000]
percent and both WHO all-age crude suicide mortality rates finite in
[0,200] per 100,000. Exposure X is asinh(sample SD of the nine
inflation rates with denominator eight, divided by 5). Outcome Y is
suicide rate_2021 minus suicide rate_2014. Controls are suicide
rate_2014 and asinh(mean 2005–2013 inflation / 5). A positive beta is
the claimed direction. Inflation is not household hardship, and death
registration, modelling, conflict, demographics, and the pandemic
limit interpretation.

## Frozen analysis and gates

For each test, fit one equal-national-area OLS with an intercept and the
named controls. Use HC3 robust standard errors and a two-sided Student
t reference with N minus fitted-column count degrees of freedom.
No imputation, nearest-year join, winsorization, geography replacement,
alternative model, weighting, subgroup, or post-result covariate choice.

| Test | Minimum complete areas | Material exposure rule | Minimum material areas | Exposure IQR minimum | Meaningful absolute beta |
| --- | ---: | --- | ---: | ---: | ---: |
| Solar / PM2.5 | 85 | absolute log1p solar-intensity change ≥0.7 | 30 | 0.50 | 0.5 micrograms/m3 |
| Education / participation | 90 | absolute spending/GDP change ≥0.5 pp | 30 | 0.50 | 1.0 participation pp |
| Inflation / suicide | 110 | raw nine-year CPI inflation SD ≥5 pp | 30 | 0.25 in asinh(SD/5) | 0.5 deaths per 100,000 |

Each test also requires full rank, positive residualized exposure and
outcome variation, finite positive HC3 uncertainty, no single area over
**15%** of squared residualized exposure or **20%** of squared
residualized outcome, and at most **two** failed leave-one-area-out fits.
Any gate failure is **INCONCLUSIVE**, with no public coefficient.
After all gates pass, **SUPPORTED** requires a coefficient in the
predeclared direction with at least the meaningful magnitude, two-sided
p≤**0.01/3**, and the same coefficient sign in at least **80%** of
successful leave-one-out fits. **REFUTED** requires the opposite
direction with the same magnitude, p, and sign-stability rules. All
other estimable outcomes are **PARTIAL**. This family-local Bonferroni
cutoff does not correct wider archive selection.

The three outcomes are distinct constructs and source tables, though population estimates enter some measures. They remain
descriptive and can respond to common shocks, reverse expectations,
measurement models, and country composition. No causal, policy,
school, position, or featured credit is awarded from any verdict.

## Strict chronology and replay

1. Commit this plan, all three specs and steelmans, the runner, and the
   three key-only rosters together before selected numeric access.
2. Verify exact source bytes, fetch manifests, dimensions, and keys;
   commit one metadata-only family source lock separately.
3. Only then open selected values. Run all three fixed designs and gates
   and commit the family result audit and nine artifacts per test.
4. Regenerate all 27 run artifacts and the family audit against the
   original hash-pinned raw vintages, passing an explicit --source-root
   checkout path to the runner or replication wrapper; compare every
   output byte for byte. Shared indexes may be refreshed after reviewed
   integration.

Official definitions: [IRENA capacity methodology](https://dashboard.irena.org/download/Methodology.pdf);
[WHO modelled PM2.5](https://www.who.int/data/gho/data/themes/air-pollution/modelled-exposure-of-pm-air-pollution-exposure);
[WDI education spending](https://data.worldbank.org/indicator/SE.XPD.TOTL.GD.ZS);
[ILOSTAT labour data](https://ilostat.ilo.org/data/);
[WDI CPI inflation](https://data.worldbank.org/indicator/FP.CPI.TOTL.ZG);
[WHO crude suicide mortality](https://www.who.int/data/gho/indicator-metadata-registry/imr-details/4664).
