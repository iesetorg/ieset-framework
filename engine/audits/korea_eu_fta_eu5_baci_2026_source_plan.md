# Blind Korea–EU5 BACI treaty-flow registration

Date: 2026-10-10. Policy record, hypothesis, steelman, this source plan, and
the guarded runner must first appear in one Git commit before a selected BACI
flow amount is read. Extract only the fixed source rows from the pinned CEPII
ZIP after that commit and commit the slice with its custody manifest in a
second commit before any contrast or result is computed.

The [European Commission](https://policy.trade.ec.europa.eu/eu-trade-relationships-country-and-region/countries-and-regions/south-korea_en)
dates provisional application of the EU–Republic of Korea FTA to 1 July 2011;
formal ratification followed in 2015. The official agreement-status metadata
in CEPII turns on for KOR→EU5 in 2012, its first full post calendar year.

Publisher: CEPII Gravity V202211 official ZIP
`https://www.cepii.fr/DATA_DOWNLOAD/gravity/data/Gravity_csv_V202211.zip`,
member `Gravity_V202211.csv`, ZIP SHA-256
`7ffea0510a536587f2f9295bbafef4a312a36b366acc256eb6d9770fe35e44b1`.
The existing tracked fetch manifest is
`data/manifests/fetch_run_2026-05-15T175027Z.yaml`; the local 197 MB ZIP is
ignored by Git. [CEPII documentation](https://www.cepii.fr/DATA_DOWNLOAD/gravity/doc/Gravity_documentation.pdf)
defines directed `tradeflow_baci` as nominal merchandise trade in thousands
of current US dollars and `fta_wto` as agreement status, not tariff intensity.
The 405-row outcome slice is a source-attributed subset and remains subject to
CEPII terms before any public redistribution.

## Frozen cells and analysis

- Treated origin: KOR. Eight fixed donor origins: JPN, TWN, CHN, MYS, THA,
  IDN, VNM, IND. Five fixed EU destinations: DEU, FRA, ITA, ESP, NLD.
- Nine annual years: 2007–2015. Exactly 9 origins × 5 destinations × 9 years
  = 405 existing-country directed cells are required. Metadata-only preflight
  found one key for every cell. It did not read a selected flow magnitude or
  value null mask.
- FTA-status preflight found KOR→EU5 zero through 2011 and one in 2012–2015;
  every donor→EU5 flag is zero throughout. That schedule is frozen.
- Source columns are CSV row ordinal, year, ISO3 origin and destination,
  origin/destination existence flags, `fta_wto`, and `tradeflow_baci`. The
  extractor retains one excess existing row if a duplicate appears, so the
  gate cannot hide a duplicate. No aggregation or contrast occurs at extraction.
- For each origin-year, sum the five directed nominal BACI flows and take
  `log1p`. The primary contrast is KOR's mean 2012–2015 log flow minus its
  mean 2007–2010 log flow, less the median of those same changes for the
  eight fixed donors. The 2011 event year is required as a source cell but
  omitted from the means.
- Require all source cells, unique existing-country rows, finite nonnegative
  flows and the exact FTA schedule. Require absolute treated minus median
  donor OLS pretrend slope gap over 2007–2010 ≤0.03 log units/year. A failed
  gate is INCONCLUSIVE and no post contrast is estimated. With gates passed,
  support means contrast ≥ln(1.15); refutation ≤−ln(1.15); else PARTIAL.

This is one treaty-level exploratory descriptive test, not five destination
tests or an inferential family. No reverse direction, product partition,
alternate donor/window, or failed-case replacement belongs to this
registration. Multiple earlier FTA screens and the KOR–USA timing are
disclosed. No p-value, causal, featured, school, or policy-score credit is
available. Price/quantity mix, exchange rates, product composition, and
concurrent reforms remain limitations.

To reproduce: commit registration; `python3 scripts/run_korea_eu_fta_eu5_baci_2026.py extract --source-zip <LOCAL_HOME>/IESET/data/raw/cepii/Gravity_csv_V202211.zip`;
commit only the slice and manifest; then use `run`, `verify`, and
`verify-source` with the unchanged runner. Keep the ZIP and broad derived
parquet outside Git.
