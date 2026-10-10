# Blind prospective design review: wealth-tax receipts and top-1 share

**State:** uncommitted prospective package only. No preregistration commit, lock, outcome
value inspection, estimation, run artifact, or verdict has occurred in this
worktree. The first spec commit, lock commit, and run must be separate in that
order. Do not treat this file as a lock.

## Question and source custody

The test asks whether OECD recurrent net-wealth-tax receipts (% GDP) at year
`t` have a negative descriptive association with WID top-1 net personal wealth
share at `t+3`. The 38 countries and 1,113 candidate pairs were fixed by
country/year keys alone for `t=1990..2020`. Exact source bytes, key digests,
roster, and derivation are in `source_roster.json`. The OECD fetch manifest is
`data/manifests/fetch_run_2026-07-23T153857Z_oecd_tax_structure.yaml`.
The WID publisher manifest is
`data/manifests/fetch_run_2026-06-29T154409Z_wid_wealth_concentration.yaml`;
the pinned outcome vintage was produced by
`scripts/_build_zucman_panel_adapters.py` from that derived panel and the raw
WID vintage. The adapter and input hashes are recorded in the roster and
publisher manifest.

Selected WID outcome preflight read only Parquet schema (`country_iso3`,
`year`, `value`) and `country_iso3`/`year` keys. It did not read outcome values,
outcome null flags, any outcome status, or published coefficient snippets.
After the design and roster were fixed, treatment-only inspection found
nonzero, within-country varying receipts in 18 of 38 countries; all 1,113
candidate treatment keys carried finite values. This did not change the roster
or the predeclared 15-varying-country floor. The merged candidate
key set has SHA256 `6bff7786bcd708321dd07fc101b84aec4bd025f3104481062dfd7c167b9e0b1e`.

## Duplicate and credit screen

Repository text search found event-specific wealth-tax/top-share candidates
for France 1981 and 2017, Spain 2011, Colombia 2022, and Norway 2022. None
uses this pinned OECD receipts series in a broad 38-country, three-year-lag
panel. The WID apex-trend spec tests a time trend, not the tax-receipts pair.
This design is therefore a distinct descriptive calibration, not a replacement
for those policy-event tests. Its `covers_claims` array is empty. It receives
zero causal, policy, school, or featured credit regardless of its label.

## Fixed analysis and stop rules

The primary coefficient comes from OLS of share at `t+3` on receipts at `t`,
country and tax-year indicators, with an explicit country-cluster CR1
covariance and two-sided Student t(`G-1`) p value. Support and refutation
both require p≤0.01 and an absolute coefficient of at least 0.5 top-1-share
percentage point per GDP-percentage point receipts. On complete cases, the
model must be full rank and residualized treatment squared-signal shares must
not exceed 20% for the largest ceiling(1%) rows, 15% for the largest country,
or 20% for the largest tax year. No
weights, extra covariates, imputation, winsorization, alternate vintage, or
value-dependent country selection are allowed. The runner reports excluded
missing/nonfinite observations and fails closed on invalid ranges or source,
key, roster, chronology, or output mismatches. It writes the standard nine run
artifacts only after a separate source-lock commit. The verdict and data gates
are frozen in the hypothesis YAML; leave-one-country-out signs are a
predeclared stability gate. A failed gate yields INCONCLUSIVE, not a favorable
label or a post-hoc revision. Exact replay regenerates all nine artifacts in
an ephemeral directory and compares byte hashes.

## Required chronology after review

1. Review this package and commit the spec, steelman, roster, audit,
   runner, and synthetic tests as the preregistration commit. The spec already
   says `pre_registered`, but has no registration timestamp until that commit.
2. In a later commit, create and commit the lock with the runner's
   `--prepare-lock` mode after checking the pinned files. Do not estimate in
   this step. The runner rejects same-commit spec and lock histories.
3. After the lock commit, invoke `--run` with a source root containing the
   exact pinned vintages. Commit the nine run artifacts only after review.
4. Invoke `--replay` against that run; retain hash comparison evidence and
   run the repository validators before any public promotion decision.

If a source is unavailable in this managed worktree, `--source-root` may point
to the primary checkout's ignored vintage files. The exact bytes and roster
must match; a new fetch or source substitution requires a new design.
