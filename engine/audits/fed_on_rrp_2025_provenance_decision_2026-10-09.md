# Fed ON RRP 2025 provenance decision — 2026-10-09

Hypothesis: `fed_on_rrp_2025_durability_holdout_v2`.

**Decision:** accept this exact local vintage for **descriptive calibration only**. Its
fetch-time acquisition transaction is unverified. The result is reproducible
against the pinned local file but is not an independent-source replication,
proof that the 2025 values were globally unseen, or evidence for the old
Treasury-bill mechanism. No causal, claim-level, or automatic scoreboard credit
is granted by this decision.

Evidence considered:

1. The frozen registration is commit `35ddec8e5fce9261ad7e8cac30b2d917c5b1b5f7`.
   Its rule fixes all four 2025 quarter medians and the source file before
   the new run. The registration commit contains no result artifacts.
2. The local `data/vintages/fred/RRPONTSYD@2026-04-30T115134Z.parquet` hashes
   to `4ed716e07b2843a319510dc5074231a33e3afe08706ebc9f6546b62624093335`.
   The previously tracked
   `engine/runs/financial_fed_reverse_repo_facility_usage_2021_2024/manifest.yaml`
   names that same file, series, publisher, and hash. This is a chain of local
   custody back to the old run, not a fetch-time source receipt.
3. [FRED's RRPONTSYD series page](https://fred.stlouisfed.org/series/RRPONTSYD)
   identifies the series as daily, in billions of US dollars, sourced from the
   Federal Reserve Bank of New York. It confirms the source identity and unit,
   not the integrity of this particular local acquisition.
4. The registered runner's read-only `--check` replay verified the result
   packet after the fit. It found 61, 62, 64, and 62 finite daily observations
   across 2025 Q1–Q4 and medians of 126.234, 155.885, 56.711, and 4.974
   billion dollars. Each quarter clears the predeclared 55-day coverage gate
   and the support threshold of less than 500 billion dollars.

The missing fetch-time manifest remains a recorded provenance limitation in
the spec, steelman, manifest, and design audit. A later source receipt or an
independent download could strengthen this evidence, but must not be silently
substituted into the frozen replay. Public tier: **calibration** if the regular
registration, replication, and integrity audit gates also pass. Canada’s
companion holdout is **INCONCLUSIVE** due to a required null value and remains
archived.
