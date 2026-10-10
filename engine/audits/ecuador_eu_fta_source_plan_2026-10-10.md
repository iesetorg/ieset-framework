# Ecuador–EU agreement: one blind five-destination export registration

Date: 2026-10-10. Commit this plan, hypothesis specification, steelman, and runner together **before reading any selected BACI tradeflow value or null mask**. A later commit must first add the exact small source slice and custody manifest. Only then may the frozen estimator run. A null, nonunique, or otherwise invalid source cell yields INCONCLUSIVE, not a repaired sample.

## Authorities and source

The [Official Journal notice](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:22016X1229(02)) dates the EU–Ecuador accession protocol's provisional application to **1 January 2017** after signature on 11 November 2016. The [Commission's Andean trade page](https://policy.trade.ec.europa.eu/eu-trade-relationships-country-and-region/countries-and-regions/andean-community_en) confirms the same date. The 2016 signing year is omitted from both comparison averages. The [EU preference bridge proposal](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:52014PC0585) is disclosed because it weakens any claim of a sharp 2017 tariff discontinuity.

Publisher: CEPII Gravity V202211, [official archive](https://www.cepii.fr/DATA_DOWNLOAD/gravity/data/Gravity_csv_V202211.zip), member `Gravity_V202211.csv`, SHA-256 `7ffea0510a536587f2f9295bbafef4a312a36b366acc256eb6d9770fe35e44b1`. The tracked provenance file is `data/manifests/fetch_run_2026-05-15T175027Z.yaml`. [CEPII's documentation](https://www.cepii.fr/DATA_DOWNLOAD/gravity/doc/Gravity_documentation.pdf) defines `tradeflow_baci` as directed merchandise trade in thousands of current US dollars and `fta_wto` as agreement status, not tariff intensity. The raw 197 MB ZIP is ignored and must not be staged. Review CEPII terms before any external publication of the small extracted slice.

## Frozen membership and key audit

- Focal origin: ECU. Comparator origins: ARG, BOL, BRA, PRY, URY. These are South American origins without a CEPII-recorded EU agreement during the fixed window; the comparators are not claimed to match Ecuador's product mix.
- EU destinations: DEU, ESP, FRA, ITA, NLD. They are pooled into **one treaty-level hypothesis**, with no destination-level verdicts.
- Source years: 2012–2019 inclusive. Pre: 2012–2015. Omitted signing year: 2016. Post: 2017–2019. The post window stops before 2020.
- Exact source grid: 6 origins × 5 destinations × 8 years = **240 distinct existing-country dyad-year keys**. Key and agreement-status inspection before registration found exactly one existing-country row per key. The source also carries 48 nonexisting-country duplicate rows for some same ISO3/year keys; the extractor excludes and counts them, but an extra *existing* row fails the gate. No selected `tradeflow_baci` value or null mask was read.
- Expected `fta_wto`: ECU to every fixed EU destination is 0 in 2012–2016 and 1 in 2017–2019; every donor dyad remains 0 in all eight years. An unexpected status fails the gate.

Earlier IESET treaty tests used this CEPII/BACI vintage and their results are known; this registration does not claim global source blindness. No selected Ecuador–EU portfolio tradeflow value or null mask was opened before registration.

The extractor selects only source CSV record ordinal, year, origin/destination ISO3, existence flags, `fta_wto`, and `tradeflow_baci` for those fixed keys. It preserves one excess existing row as duplicate evidence, computes no outcome contrast, and emits a SHA-256 manifest. The source ZIP hash, extracted bytes, key roster, and registration chronology are checked before a verdict. A changed ZIP, incomplete grid, duplicate existing-country key, or outcome completeness failure is INCONCLUSIVE.

## Frozen estimator and disposition

Let `L(o,d,y) = ln(1 + tradeflow_baci(o,d,y))`. For each origin–destination dyad, compute its mean `L` in 2017–2019 less its mean in 2012–2015. For each destination, subtract the **median** of the five donor-origin changes from ECU's change. The primary contrast is the **median** of those five destination-level differences. All 240 cells must pass source, existence, FTA-status, and finite nonnegative tradeflow checks.

The pretrend gate uses only 2012–2015: for each year and destination, subtract the median donor `L` from ECU `L`; then take the median of those five destination gaps. The absolute OLS slope of this four-year pooled gap series must be ≤0.03 log units per year. This gate is checked before direction. If it fails, return INCONCLUSIVE. If gates pass, SUPPORTED requires primary contrast ≥ln(1.15); REFUTED requires ≤−ln(1.15); otherwise PARTIAL. There is no p-value or causal inference. Destination components are diagnostics of this **one** test, never separately counted or promoted. No reverse direction, alternate window, donor replacement, product partition, threshold search, or second result card is permitted.

This test can add at most one public descriptive calibration. It grants zero causal, featured, school, and policy-score credit. Nominal flows mix prices and quantities. Destination demand, product composition, Ecuador's 2016 earthquake, and contemporaneous policy or exchange-rate changes remain confounding. The temporary EU preference bridge also limits policy-shock interpretation.

## Execution contract

1. Commit the immutable specification, steelman, this plan, and `scripts/run_ecuador_eu_fta_2017.py` together. Do not include source slice or results.
2. Extract from the exact source ZIP after registration; commit only `data/pinned_evidence/ecuador_eu_fta_2017.csv` and `.manifest.json` in a later commit. Do not stage the raw ZIP or derived parquet.
3. Run unchanged rules; preserve INCONCLUSIVE if a gate fails. Verify byte-exact artifacts and re-extract the source slice byte-for-byte. Regenerate public ledgers only for a passing gate and keep credit at zero.
