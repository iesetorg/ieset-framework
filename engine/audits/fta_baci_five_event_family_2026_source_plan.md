# Five CEPII/BACI treaty-event descriptive registrations

Date: 2026-10-09. All five case specifications, steelmen, this source plan, and
the shared guarded runner must first appear in one Git commit before any selected
BACI flow magnitude is read. The source slice must be extracted from the
byte-pinned CEPII archive only after that commit, and added in a second commit
before any outcome analysis. The runner enforces those steps and byte-exact replay.

Publisher: CEPII Gravity V202211, official archive
https://www.cepii.fr/DATA_DOWNLOAD/gravity/data/Gravity_csv_V202211.zip
(member Gravity_V202211.csv), SHA-256
7ffea0510a536587f2f9295bbafef4a312a36b366acc256eb6d9770fe35e44b1.
The pre-existing tracked manifest is
data/manifests/fetch_run_2026-05-15T175027Z.yaml.
CEPII documents tradeflow_baci as directed merchandise trade in thousands of
current US dollars and fta_wto as agreement status, not tariff intensity:
https://www.cepii.fr/DATA_DOWNLOAD/gravity/doc/Gravity_documentation.pdf .

The only selected source fields are CSV row ordinal, year, origin ISO3,
destination ISO3, origin/destination existence flags, fta_wto, and
tradeflow_baci. The extractor retains exactly the fixed dyad-year keys with
both existence flags equal to one. It records every raw key match and excluded
nonexisting row, preserves one excess existing row to prove a duplicate, and
does not calculate any contrast during extraction. A changed source ZIP,
missing/duplicate key, missing/negative flow, or changed FTA status cannot be
repaired after observing values.

## Fixed case family

| Case | Effective date | Directed treated dyad | Seven/eight fixed donor origins to same destination | Four pre years | Four post years | Old result |
| --- | --- | --- | --- | --- | --- | --- |
| chile_us_fta_bilateral_exports_2004_v2 | 2004-01-01 | CHL→USA | ARG, BOL, BRA, ECU, PRY, URY, VEN | 2000–2003 | 2005–2008 | trade_lib_chile_bilateral_fta_cascade REFUTED |
| colombia_us_fta_bilateral_exports_2012_v2 | 2012-05-15 | COL→USA | ARG, BOL, BRA, ECU, PRY, URY, VEN | 2008–2011 | 2013–2016 | trade_lib_colombia_us_fta_2012 SUPPORTED |
| korea_us_fta_bilateral_exports_2012_v2 | 2012-03-15 | KOR→USA | JPN, TWN, CHN, MYS, THA, IDN, VNM, IND | 2008–2011 | 2013–2016 | trade_lib_korus_2012_us_korea_trade PARTIAL |
| new_zealand_china_fta_bilateral_exports_2008_v2 | 2008-10-01 | NZL→CHN | AUS, USA, CAN, JPN, KOR, IND, DEU | 2004–2007 | 2009–2012 | No direct old case identified |
| australia_china_fta_bilateral_exports_2015_v2 | 2015-12-20 | AUS→CHN | USA, CAN, JPN, TWN, IND, DEU, FRA, ITA | 2011–2014 | 2016–2019 | trade_lib_chafta_australia_china_2015 PARTIAL |

The five case memberships contain 378
dyad-year slots; overlapping donor rows are stored once, giving
359 unique expected source keys. Every source key,
existence flag, null mask, and agreement-status schedule was checked before
registration without reading a held-out BACI magnitude. The effective dates
are from the official sources embedded in each case's registered steelman.
The event year is omitted for all cases. For the late-year NZ-China and
Australia-China agreements, CEPII first records fta_wto=1 in the next full
calendar year; the registered event-year expected flag is zero.

## Frozen estimator and gate

For each directed dyad, take natural log of 1 plus the BACI flow in thousands
of current US dollars. The primary contrast is the treated dyad's four-year
post mean less its four-year pre mean, minus the median of the fixed donor
dyads' corresponding changes. Require all nine annual cells per dyad,
including event year, with unique existing-country rows, finite nonnegative
flow, and the exact registered fta_wto schedule. Require absolute treated
minus median donor OLS pretrend slope gap at most 0.03 log units per year,
matching the earlier Peru treaty rule. These gates are checked before the
directional verdict. If any gate fails, the case is INCONCLUSIVE and archived.
If all pass, SUPPORTED means contrast at least ln(1.15), REFUTED at most
minus ln(1.15), and PARTIAL otherwise.

This is one closed family of five treaty-level tests. No reverse-direction
flows, alternate windows, tariff products, donor replacements, threshold
changes, or same-event duplicate claims may be added to this registration.
No p-value or causal inference is made. Any later inferential follow-up needs
a new registration and a five-test family-wise two-sided alpha budget of
0.05/5=0.01; the small donor-permutation sets here cannot reach that cutoff.
At most five public descriptive calibration cards and zero featured, school,
or policy-score credits can arise. Failed pretrends or source gates reduce
that ceiling. The four older WDI country-outcome result cards are known and
are disclosed, not used to choose signs or donor sets.

## Execution and reproduction

1. Commit all five hypothesis YAMLs, steelmen, this plan, and
   scripts/run_fta_baci_five_event_family_2026.py together. Keep the source
   slice and all result artifacts out of this commit.
2. Run the committed script's extract command against the exact official ZIP.
   Commit only data/pinned_evidence/fta_baci_five_event_family_2026.csv and
   its .manifest.json in a second commit. The 197 MB ZIP and 84 MB local
   derived parquet remain outside Git.
3. Run all five cases with the unchanged shared runner. Inspect every
   verdict, including INCONCLUSIVE. Verify all run artifacts byte-for-byte
   and independently re-extract the slice byte-for-byte from the ZIP.
4. Commit the exact run artifacts and regenerated evidence ledgers. No
   school or policy-score credit is permitted from this family.

The source family ends before a usable 2021 BACI outcome in this vintage.
Australia's post window ends in 2019 to exclude the 2020 COVID shock. The
nominal flow still mixes prices and quantities, and fixed same-destination
donors do not remove product mix, exchange rates, commodity cycles, or
other concurrent policy changes.
