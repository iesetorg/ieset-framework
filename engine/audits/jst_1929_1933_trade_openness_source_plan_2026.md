# Blind source and decision plan: JST interwar advanced-economy trade share

## Question and claim fit

This is one prospective descriptive contrast prompted by the archived `trade_lib_smoot_hawley_1930_historical` record. The archived run is not repaired, relabelled, or counted. The new ID tests only an advanced-economy trade-to-GDP fall around 1929–1933. It does not test the tariff's effect, global nominal trade, retaliatory policy, or a century-wide peacetime rank. The original named 14-country sample contains Argentina and Brazil, which are absent from JST R6. The other twelve named economies form the exact roster; no later substitutions.

The publisher's [JST R6 database page](https://www.macrohistory.net/database/) lists nominal GDP, imports, and exports in local currency. This supports within-country `(imports+exports)/gdp` without conversion. The original licensed parquet is `jst_macrohistory@2026-05-05T195309Z.parquet`, SHA-256 `4219d53e595e50b05430b5e4edd91f5f9ebff3987e3d0b6f21d2f2f50bc03a6f`, from the tracked 2026-05-05 fetch manifest. Source URL: `https://www.macrohistory.net/app/download/9834512569/JSTdatasetR6.xlsx`. Cite Jordà, Schularick and Taylor (2017). Preserve the publisher's CC BY-NC-SA 4.0 conditions. The raw file is Git-ignored and is not redistributed; exact replay needs a lawfully held copy with the recorded hash.

## Frozen sample and estimator

Twelve ISO3 codes, sorted: AUS, BEL, CAN, DEU, ESP, FRA, GBR, ITA, JPN, NLD, SWE, USA. Each has every annual key 1925–1933 in the source-only key screen, 108 country-year keys total. Only keys and schema, never imports/exports/GDP values or null masks, were inspected before registration. All nine selected values in each of the three fields must be finite and strictly positive for a country to count. No gap-fill, trim, alternate vintage, or replacement. The panel must retain at least ten complete countries. At least eight complete countries must have a one-percentage-point annual range in their nine-year trade/GDP series.

Define `r(c,y) = 100*(imports+exports)/gdp`. Define `d(c) = mean(r(c,1925:1929)) - mean(r(c,1932:1933))`. The primary statistic is the equal-country mean of `d(c)` among complete countries. Years 1930–1931 are used only for completeness and within-country range. The maximum absolute shift from the full mean across every leave-one-country-out mean must be at most three percentage points; every LOO mean must have the same sign as the full mean. Failed source, sample, variation, or influence gate means INCONCLUSIVE, not a rescued numerical estimate.

If all gates clear, SUPPORTED requires mean decline at least eight percentage points and at least eight countries with positive declines. REFUTED requires mean decline below five points. All other valid cases are PARTIAL. The support/refutation thresholds come from the archived claim's trade-to-GDP magnitude bands, with new breadth and influence safeguards. One closed descriptive family, no inferential alpha. Report aggregate mean decline, complete-country count, positive-decline count, variation count, LOO range, gate disposition, and limitations; do not publish raw or country-level values.

## Custody sequence

1. Commit the v1 spec, steelman, this plan, and exact analytic runner as one registration commit. The code's `plan` command may read only `country_iso3` and `year` from the selected parquet to verify the 108-key roster.
2. Run `source-lock --source-parquet <local-source-root>/data/vintages/jst/jst_macrohistory@2026-05-05T195309Z.parquet`. It writes only publisher, hash, size, schema, key-roster hash, and registration Git SHA. Commit that manifest in a later source-lock commit. This phase must not read selected values or null masks.
3. Only after the lock is committed, run `run` with the same exact source. The runner enforces Git ordering and byte identity of registration and lock, then opens only the fixed fields and years. Commit the aggregate result separately. `verify` recomputes from the same exact source and compares result bytes. No raw or per-country series are committed.

A failure at any stage stays a documented no-go or INCONCLUSIVE. No result receives policy, causal, school, position, or featured credit from this descriptive family.
