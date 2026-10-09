# Additional policy and time-series review of the 500-case v2 queue

Date: 2026-10-09. This is a design audit, not an estimated result or a public
graduation. It excludes the Spain, Argentina, and Germany cases reviewed in
`prospective_v2_500_policy_event_holdout_review_2026-10-09.md`. Old result
cards and replication code were read. Candidate endpoint values, coefficients,
signs, and null masks were **not** read in this lane. Parquet schemas, source
hashes, manifests, and date/country/dimension keys were checked. All proposed
v2s must disclose the old result and receive at most descriptive calibration
credit after a committed registration and exact replay.

## Ranked follow-ups

### 1. Canada 2024–25 real GDP per capita relative to fixed peers — draft ready, values unexamined

- Old ID: `canada_gdp_per_capita_stagnation_post_2015` (queue rank 2). The
  old same-commit result was `SUPPORTED`; its replication code hard-coded a
  2000–2023 estimation window and the six peers USA, AUS, NZL, GBR, NOR, CHE.
  The new proposed ID is `canada_gdp_pc_2024_2025_peer_holdout_v2`.
- New endpoint: the 2024→2025 log change in WDI constant-PPP real GDP per
  capita (`NY.GDP.PCAP.PP.KD`) for CAN minus the unweighted median of the six
  fixed peers' exact same change. Require all **14** finite positive values;
  country-year key presence was confirmed but is **not** value completeness.
- Frozen rule: support further one-year stagnation only if Canada's own
  log change is nonpositive **and** its peer gap is at most -0.01. Refute if
  Canada's change is positive and its gap is at least +0.01. Otherwise partial;
  any missing/invalid endpoint is inconclusive. No p-value or causal language.
- Source custody: `data/vintages/world_bank_wdi/NY.GDP.PCAP.PP.KD@2026-05-05T194648Z.parquet`,
  SHA-256 `6432d570bd5e7d94d659d310c48454caedb7b105db0bfeebbe1e44189c63ecfb`,
  tracked `data/manifests/fetch_run_2026-05-05T200056Z.yaml` with the exact
  World Bank API source URL. The raw parquet is ignored by Git and must be
  available for exact local replay.
- Limit: one later interval on the *same* WDI indicator and old peer roster.
  It neither tests the whole post-2015 trend anew nor identifies Canadian
  policy, productivity, or population mechanisms. The old code loaded a
  full source file before filtering its 2023 endpoint, so no claim of global
  blindness is made.

### 2. Fed ON RRP 2025 low-usage durability — draft ready, fetch custody incomplete

- Old ID: `financial_fed_reverse_repo_facility_usage_2021_2024` (queue rank
  116). The old `SUPPORTED` run's dispositive code used the 2021–23 peak and
  2024-Q3 low. The new ID is `fed_on_rrp_2025_durability_holdout_v2`.
- New endpoint: the four separate 2025 calendar-quarter medians of daily
  FRED `RRPONTSYD` amounts, in USD billions. Structural key preflight found
  **261** 2025 dates (64, 65, 66, 66 by quarter), but did not inspect amounts
  or missingness. Require at least 55 unique finite nonnegative amounts per
  quarter after registration.
- Frozen rule: support durability if all four quarter medians are below
  USD 500 billion; refute a rebound if at least two are at or above USD
  1,000 billion; otherwise partial. It cannot adjudicate the old Treasury
  bill absorption mechanism.
- Source custody: `data/vintages/fred/RRPONTSYD@2026-04-30T115134Z.parquet`,
  SHA-256 `4ed716e07b2843a319510dc5074231a33e3afe08706ebc9f6546b62624093335`.
  The tracked older `engine/runs/financial_fed_reverse_repo_facility_usage_2021_2024/manifest.yaml`
  records that exact file, publisher, series, and SHA. [FRED's official
  series page](https://fred.stlouisfed.org/series/RRPONTSYD) confirms its
  daily frequency and USD-billion units. **No fetch-time manifest for this
  local slice was found**; the source acquisition transaction remains
  unverified. That provenance limit is frozen in the spec and output packet,
  and must be resolved or explicitly accepted by the provenance gate before
  any graduation claim.
- Limit: later measurement from the same vintage, not an independent source
  replication. The old runner loaded the full file before date filtering;
  only the old *result* window is disjoint. No causal policy credit.

### 3. Eurozone 2008–14 bottom-quintile/poverty comparison — new descriptive design possible, no draft

- Old ID: `eurozone_austerity_distributional_incidence` (queue rank 380).
  Its old run was **inconclusive/data gap**: it required `ilc_peps01n`; its
  selected `ilc_di12` Gini vintage begins in **2014**, so a 2008→2014 Gini
  change is impossible. It did not fit the distributional endpoint. The
  named Alesina-Favero-Giavazzi narrative consolidation-shock panel is still
  absent. Treating IMF `GGXCNL_NGDP` net lending as that shock would be a
  different and weaker treatment measure.
- A narrower, **noncausal** new ID could use direct Eurostat
  `ilc_di01` income-share keys (`quantile=QU1`, `indic_il=SHARE`, fixed
  currency=`EUR`) and `ilc_li02` at-risk-of-poverty keys
  (`unit=PC`, `indic_il=LI_R_M60`, `sex=T`, `age=TOTAL`) for 2008 and
  2014. Both exact selectors have **22 structural country-year keys** for the
  five old periphery and six old core countries. This measures bottom-quintile
  share and relative poverty directly, not the old missing Gini or a causal
  austerity incidence. Eurostat describes [the quantile dataset](https://ec.europa.eu/eurostat/databrowser/view/ilc_di01/)
  and [the poverty threshold](https://ec.europa.eu/eurostat/databrowser/view/ILC_LI02/).
- Exact local files and tracked manifests are `ilc_di01@2026-04-30T115754Z`
  (SHA-256 `6dc9948f57c6dc32e967628f541bbb19c894680ae7304b9de59fd50e641c29b5`,
  `fetch_run_bootstrap_2026-04-30T121833Z.yaml`) and
  `ilc_li02@2026-05-05T205827Z` (SHA-256
  `f49a93b5183acddb13c89b07bba923693eee92a31cf7f065bd0e652e52ea4648`,
  `fetch_run_2026-05-05T210519Z.yaml`). A future draft must freeze a joint
  directional rule, complete-value gate, and disclosure that 2008–14 is the
  old intended window and not an out-of-time holdout. No outcome value or
  missingness has yet been inspected for this redesign.

## Shortcuts that remain blocked

| Old queue case | Exact blocker |
| --- | --- |
| `eurostat_construction_supply_housing_cost_relief_panel` | The old generic 25-country panel used a broad OECD dashboard. Its direct `MEASURE=3_3` housing-cost-overburden series has **zero 2025 keys** in the pinned July dashboard vintage; the many 2025 rows are mostly other well-being measures. A 2025 direct-outcome holdout cannot use this file. |
| `eurostat_interest_spending_public_investment_tradeoff_panel` | The old generic run treated IMF public debt as interest expenditure and WDI *total* investment as public investment. Current pinned Eurostat list lacks the direct government interest/public-investment pair; extending the proxy would repeat the semantic error. |
| `canada_real_disposable_income_post_2015` | Its ideal OECD household disposable-income outcome was missing in the old run, and the current named WDI GNI proxy does not measure after-tax household purchasing power or housing-net income. A later proxy year cannot repair that claim. |
| `tax_inequality_biden_ctc_2021_child_poverty` | The pinned US Census SPM child-poverty file ends in 2023. The old test already used 2020–22; there is no 2024–25 direct child-SPM temporal holdout in this local vintage. |
| `uk_truss_mini_budget_currency_sovereign_mechanism` | The old run lacked the predeclared 30-year gilt yield. Current BoE vintages still lack `IUDLG7N`; another 10-year/FX rerun would repeat the surrogate and cannot identify institutional versus hard fiscal limits. |
| `financial_negative_rates_eurozone_2014_2022` | The pinned ECB data support a *different* 2023–25 DFR/Euribor reversal description, but the original household-deposit and core-sovereign-yield gates remain absent. M3 is not household deposits. Do not rebrand a reversal description as validation of the old negative-rate composite. |
| US yield-curve, Baa–Aaa, JOLTS, mortgage-rate episode studies | The April 2026 FRED snapshots provide too little new completed 12- or 24-month follow-through to produce a genuinely out-of-time episode replication; old historical episodes and outcomes were already evaluated. |

The two authored drafts have a joint guarded runner and structural tests. They
remain uncommitted and unfitted. The runner's `--preflight` reads only source
hashes and dimension keys; `--run` requires both new specs, both steelmen, and
the runner in one unchanged first-addition commit, with no result artifacts in
that commit. `--check` is a read-only replay of the complete stored packet.
