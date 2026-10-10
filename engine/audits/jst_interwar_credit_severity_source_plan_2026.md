# Frozen source and analysis plan — JST interwar credit intensity, 2026-10-10

This registration fixes a two-test **descriptive** family before inspecting
selected loan, nominal GDP, real GDP per person, or CPI values or null masks.
It asks whether more private credit relative to output at the 1929 entry year
coincides with deeper real and price-level losses through 1933 across the
original 18 JST R6 advanced economies. The two outcome records are one
correlated research family; no causal or policy conclusion is registered.

## Source custody and exact keys

Source: Jordà-Schularick-Taylor Macrohistory Database R6, the existing
manifest-pinned local Parquet vintage
`jst_macrohistory@2026-05-05T195309Z.parquet`, SHA-256
`4219d53e595e50b05430b5e4edd91f5f9ebff3987e3d0b6f21d2f2f50bc03a6f`.
Fetch manifest: `data/manifests/fetch_run_2026-05-05T200056Z.yaml`.
Publisher download and documentation:
https://www.macrohistory.net/app/download/9834512569/JSTdatasetR6.xlsx ;
https://www.macrohistory.net/database/ .
The publisher describes R6 as 18 advanced economies, annual since 1870,
with nominal private loans, nominal GDP, real GDP per person, and a CPI index.
Citation: Jordà, Schularick and Taylor (2017), *Macrofinancial History and
the New Business Cycle Facts*. License: CC BY-NC-SA 4.0. Keep licensed raw
and country-level values local; commit only source metadata and aggregate
test statistics.

Freeze exactly 18 ISO3 countries in both hypothesis specs and only 1929 and
1933. The 36 country-year keys and six field types are checked without
reading selected values. The two source-lock JSON files must be added in
successive commits **after** the single registration commit and **before**
the shared result commit. Each lock must contain the same raw SHA-256,
key-roster SHA-256, schema, and registration commit, and its own hypothesis ID.

## Fixed analysis and family error rule

Treatment: `100*tloans_1929/gdp_1929`, percentage points. Outcomes:
`-100*log(rgdpmad_1933/rgdpmad_1929)` and
`-100*log(cpi_1933/cpi_1929)`, positive for loss. The two tests use the
same complete-case country set, requiring strictly positive finite
treatment components and both outcome fields at both endpoints. No
imputation, alternative source, countries, years, weighting, trimming,
controls, model search, or selected country display. Require at least 12
complete countries, at least 20 percentage points of treatment spread, and
at least 5 log percentage points of each outcome's loss spread. Failure is
INCONCLUSIVE.

Each result uses Spearman rank correlation, average ranks for ties, and a
two-sided 99,999-draw permutation test with fixed seed 20261010 for real
output and 20261011 for CPI. Correct the two-test family at p<=0.025
per test. SUPPORTED requires rho>=0.4 and every leave-one-country-out rho
positive; REFUTED requires rho<=-0.4 and every leave-one-country-out rho
negative. Both directional verdicts also require corrected p<=0.025.
Otherwise a valid test is PARTIAL. Report the sample and spread gates,
rho, permutation p, and leave-one-out range only as aggregates.
There are no country-level hypotheses or independent-replication claims.

The earlier JST 1929–1933 trade-to-GDP calibration overlaps countries and
years but neither observes this exposure nor selects these outcome-specific
rules. This follow-up cannot be used to claim trade, credit, tariff, or
monetary causation; shared Depression shocks remain unseparated.
