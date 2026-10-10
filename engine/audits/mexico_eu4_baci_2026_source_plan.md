# Mexico–EU4 goods-flow registration and source custody

Date: 2026-10-10. This is a blind design registration, not an estimated result or public graduation. The archived `trade_lib_mexico_eu_fta_2000` WDI openness result was REFUTED and remains archived. The [European Commission](https://policy.trade.ec.europa.eu/eu-trade-relationships-country-and-region/countries-and-regions/mexico_en) dates the goods provisions to **October 2000**, correcting the old July 2000 date. The new, narrower outcome is Mexico-origin merchandise exports to **Germany, France, Spain, and Italy together**, not the whole EU.

Publisher: CEPII Gravity V202211, official archive `https://www.cepii.fr/DATA_DOWNLOAD/gravity/data/Gravity_csv_V202211.zip`, member `Gravity_V202211.csv`; source ZIP SHA-256 `7ffea0510a536587f2f9295bbafef4a312a36b366acc256eb6d9770fe35e44b1`. Existing tracked fetch manifest: `data/manifests/fetch_run_2026-05-15T175027Z.yaml`. CEPII [documentation](https://www.cepii.fr/DATA_DOWNLOAD/gravity/doc/Gravity_documentation.pdf) defines `tradeflow_baci` as directed merchandise trade in thousands of current US dollars and `fta_wto` as agreement status, not tariff intensity.

## Frozen roster and gate

- Treated origin MEX; donor origins **USA, CAN, JPN, KOR, AUS, NZL**. Destinations **DEU, FRA, ESP, ITA** for every origin. Years **1996–2004**, with pre 1996–99, post 2001–04, and late-2000 event year required but omitted from the mean contrast. Exactly **252** fixed origin-destination-year keys.
- A key-only scan of the unchanged CEPII ZIP found every key and exactly one existing-country row per key. There were **315 raw matches**, of which 63 carried nonexisting-country flags. For each destination, `fta_wto` was 0 for MEX through 2000 and 1 from 2001–04; every donor status was 0 throughout. The scan did **not** open selected `tradeflow_baci` values or null masks.
- After source lock, each of the 252 eligible directed rows must have a finite nonnegative BACI flow. For each origin-year, sum the four destination flows before `ln(1+sum)`. The four-year post minus pre log mean for MEX less the median of the six fixed donor changes is the contrast.
- Pretrend gate: absolute difference between MEX four-year pre log slope and median donor pre log slope at most **0.03 log units/year**. A structural, flow-completeness, status, or pretrend failure is **INCONCLUSIVE**. With all gates passed, **SUPPORTED** is contrast ≥ln(1.15), **REFUTED** is contrast ≤−ln(1.15), otherwise **PARTIAL**.
- This is one closed descriptive treaty family: family size **1**. There is no p-value or inferential family-wise claim. Any later inferential testing needs a new frozen registration and a two-sided family-wise alpha ≤0.05. No reverse direction, destination, donor, window, or product variant may be added to this family. Public ceiling is **one descriptive calibration record**, zero causal/featured/school/position/policy score credit.

## Custody sequence

1. Add and commit the hypothesis YAML, steelman, this plan, and the guarded runner together. Keep the extracted source slice and run artifacts absent from that first-addition commit.
2. Run the unchanged extractor only after step 1. It checks the official ZIP SHA, preserves the 252 fixed eligible records plus at most one excess eligible record to expose a duplicate, and records selection counts. Commit the small source CSV and its manifest together in a later source-lock commit. Do not stage the 197 MB local ZIP.
3. Run the unchanged estimator only after step 2. Report every verdict, including INCONCLUSIVE, and verify artifacts byte-for-byte against exact replay and source re-extraction. A clean descriptive result may be considered for the calibration ledger only after the public gate review.

Nominal BACI flows mix prices and quantities. The destination basket omits other EU countries and services. Same-destination donors cannot remove product mix, exchange rates, NAFTA-related dynamics, or all EU-specific shocks. No treaty effect is identified.
