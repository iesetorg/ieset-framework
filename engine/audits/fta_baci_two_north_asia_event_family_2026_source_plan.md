# Two distinct Australia–North Asia agreement flow registrations

Date: 2026-10-09. Both case specifications, steelmen, this plan and the shared guarded runner must first appear in one Git commit before any selected BACI flow magnitude is read. Extract the exact small source slice from the byte-pinned CEPII ZIP only after that commit. Commit the slice and custody manifest separately before running either case. The runner enforces both commits and byte-exact replay.

Publisher: CEPII Gravity V202211, official archive https://www.cepii.fr/DATA_DOWNLOAD/gravity/data/Gravity_csv_V202211.zip (member `Gravity_V202211.csv`), ZIP SHA-256 `7ffea0510a536587f2f9295bbafef4a312a36b366acc256eb6d9770fe35e44b1`. Tracked source manifest: `data/manifests/fetch_run_2026-05-15T175027Z.yaml`, which records CEPII Gravity database license/terms and the same input ZIP hash. CEPII documentation https://www.cepii.fr/DATA_DOWNLOAD/gravity/doc/Gravity_documentation.pdf defines `tradeflow_baci` as directed merchandise trade in thousands of current US dollars and `fta_wto` as agreement status rather than tariff intensity. The local 197 MB ZIP is ignored and must not be staged. Source license/terms govern publication of the extracted 126-row slice; this small provenance subset contains country-year trade values and must receive normal source-attribution review before public release.

Only source CSV ordinal, year, origin/destination ISO3, both country-existence flags, `fta_wto` and `tradeflow_baci` are selected. The extractor keeps fixed dyad-year keys with both existence flags 1, records raw matches and excluded nonexisting rows, and keeps one excess existing row to expose duplicates. It computes no outcome contrast. A changed ZIP, missing/duplicate key, missing/negative flow or different FTA status yields INCONCLUSIVE under the frozen run rule.

## Closed two-case family

| Case | Effective date and official authority | Treated dyad | Fixed donor origins to same destination | Pre years | Post years | Event-year FTA flag |
| --- | --- | --- | --- | --- | --- | --- |
| `australia_korea_kafta_bilateral_exports_2014` | KAFTA 2014-12-12, [DFAT](https://www.dfat.gov.au/trade/agreements/in-force/kafta/korea-australia-fta) | AUS→KOR | RUS, BRA, ARG, ZAF, SAU, MEX | 2010–2013 | 2015–2018 | 0 |
| `australia_japan_jaepa_bilateral_exports_2015` | JAEPA 2015-01-15, [DFAT](https://www.dfat.gov.au/trade/agreements/in-force/jaepa/japan-australia-economic-partnership-agreement) | AUS→JPN | USA, RUS, BRA, ARG, ZAF, SAU | 2011–2014 | 2016–2019 | 1 |

Each case requires nine annual cells for the treated dyad and each of six donors: 63 per case, 126 distinct fixed source keys. Metadata and null-mask screening before registration showed every key present as one existing-country row, every `tradeflow_baci` non-null, donor `fta_wto=0` throughout, and treated status 0 in the four pre years, the listed event-year status, then 1 in the four post years. No selected trade-flow magnitude was inspected. Donors and years are fixed now; no later substitution is allowed.

## Frozen estimator and disposition

Take `log1p(tradeflow_baci)` for each source row. The primary contrast is the treated dyad's four-year post mean minus four-year pre mean, less the median of six fixed donor changes to the same destination. Require all nine annual cells per dyad, unique existing-country rows, finite nonnegative flow and exact FTA-status schedule. Require absolute treated minus median-donor OLS pretrend slope gap ≤0.03 log units per year. A failed source or pretrend gate is INCONCLUSIVE and remains archived. With gates passed, SUPPORTED requires contrast ≥ln(1.15), REFUTED ≤−ln(1.15), and PARTIAL otherwise. The event year is never used in either mean.

This is one closed two-test family, with no reverse direction, product partition, alternative window/donor/threshold, or duplicate outcome cards. If a future inferential claim were contemplated, two-sided family-wise alpha would be 0.05/2=0.025, but six-donor exact permutation cannot attain that cutoff. These cards are descriptive calibrations only, with zero causal, featured, school or policy-score credit. The two outcomes share AUS as exporter, the CEPII vintage, most donors and adjacent years. They are correlated; two passing results would not provide independent replication.

The earlier five-case BACI screen is known: AUS→CHN ChAFTA was INCONCLUSIVE from failed pretrend; the other four cases are not reused. The older country-level WDI ChAFTA case was PARTIAL. These two later tests target KAFTA and JAEPA, legally distinct agreements in the existing Australian three-agreement policy bundle. The earlier outcomes were not used to alter any failed case, threshold or source. Both new tests still face Australian commodity prices, exchange rates and partner demand. Nominal flows cannot separate prices from quantities, and same-destination donors do not make the contrast causal.

## Execution

1. Commit the two specs, steelmen, plan and `scripts/run_fta_baci_two_north_asia_event_family_2026.py` together. Keep slice and result directories absent.
2. Run the unchanged runner's `extract` command against the verified official ZIP. Commit only its two custody files in a later commit.
3. Run both unchanged rules, retain every verdict, verify all generated artifacts byte-for-byte and re-extract the source slice byte-for-byte from the ZIP. Commit only the two result directories. Shared public ledgers remain under root review.
