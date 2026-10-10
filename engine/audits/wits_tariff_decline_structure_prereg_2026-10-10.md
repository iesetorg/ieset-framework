# Prospective tariff-decline and later structure family

This page freezes the value-blind design for four descriptive calibrations.
The common exposure is the 2005 minus 2010 weighted mean applied merchandise
tariff, so a positive value is a reported tariff decline. The four later
outcomes are 2010–2019 changes in manufacturing value added/GDP, industrial
employment share, manufactures/merchandise exports, and gross fixed capital
formation/GDP. They test production, labor allocation, export composition,
and capital formation. These outcomes are correlated and are **not four
independent confirmations** of trade policy effects.

The source-key roster is the sorted ISO 3166-1 alpha-3 entities from
`pycountry` 24.6.1 that have exact 2000, 2005, 2010, and 2019 row keys in
each selected source. It contains 215 codes. The roster is a key screen,
not a measured sample: no selected value, missingness mask, observation
status, coefficient, or fit was opened before registration. Aggregate
regions without ISO codes are excluded. Territories with ISO codes remain
eligible if all measured cells pass the frozen rules.

Each endpoint uses its own complete-case sample from that same 215-code
roster. Require finite 2005 and 2010 tariffs in [0,100], positive 2010
real GDP per person, and outcome levels in [0,100] at 2000, 2010, and
2019. The outcome is the 2019 minus 2010 share in percentage points.
Observation-status fields are retained in the pinned source slice for audit
but are not an additional exclusion criterion; the numeric validity rules
above are the complete eligibility rule.
The pretrend is the 2010 minus 2000 share. Fit equal-country OLS of later
change on tariff decline per five tariff percentage points, 2005 tariff,
log 2010 real GDP per person, 2010 outcome level, and 2000–2010 outcome
pretrend. Use HC3 uncertainty and two-sided Student t reference with N−6
degrees of freedom. No interpolation, winsorisation, alternate year,
country, source, outcome or model search.

For each endpoint, INCONCLUSIVE precedes any verdict if N<45, fewer than
10 countries have a decline of at least 2 points, fewer than 10 have a
decline below 2 points, tariff-decline interquartile range <1 point,
rank fails, largest residualized-exposure share >0.20, HC3 is invalid,
or more than 10% of leave-one-country-out fits fail. A valid result is
SUPPORTED only when the coefficient is positive, at least the endpoint's
registered meaningful threshold, p≤0.0025, and at least 75% of successful
leave-one-country-out coefficients are positive. REFUTED requires the
symmetrical negative result. Otherwise PARTIAL. The four-test denominator
is fixed even if some endpoints are inconclusive. Thresholds are 0.5
outcome percentage point per five tariff points for value added, industrial
employment and fixed investment; 1.0 point for manufactures export share.

Existing archive candidates visible before this design include
`wits_tariff_protection_manufacturing_upgrade_panel` and the later-outcome
tariff-duration test. This is a different exposure and horizon, not
independent replication of those claims. Import-weighted average tariffs
change when import composition changes; neither the treatment nor controls
identify a tariff reform. Industrial employment includes construction and
mining, export *share* can change with commodity prices, and gross fixed
capital formation includes public investment. Country-level confounding
and the prior archive-wide search remain material. All verdicts are
descriptive calibrations with zero causal, policy, school, position and
featured credit.

The selected raw vintages have tracked fetch manifests; the runner verifies
exact manifest and Parquet SHA-256 bytes, country-year keys, registration
commit, later source lock, and byte-for-byte replay. Source metadata and
indicator definitions are in the four YAML specifications. The source
slice is written only after registration is committed; the measured result
is written only after a separate lock commit.
