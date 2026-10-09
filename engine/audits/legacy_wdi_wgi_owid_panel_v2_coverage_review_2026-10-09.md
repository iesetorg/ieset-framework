# Legacy WDI/WGI/OWID panel v2 coverage review — 2026-10-09

This is a coverage and design audit of 146 of the 500 selected `legacy_same_commit` cases: panel FE, panel FE decomposition, or local projections with a loaded WDI, WGI, or OWID series. The old results were visible. The 146 row disposition table is in the companion CSV. No holdout model was fit and no holdout coefficient was computed. An earlier exploratory availability screen did read value columns to count finite/nonmissing records across candidate series, without printing or reviewing their magnitudes; its figures have been withdrawn. Candidate selection and the three numeric minimum-sample gates were calibrated after seeing those availability patterns. This limits the prospective strength of the registration despite no outcome magnitudes, signs, or coefficients being seen. The current preflight reads only country/year keys from pinned files and its coverage figures are upper bounds, not complete-case sample sizes.

## Disposition

| Disposition | Cases |
| --- | ---: |
| `key_envelope_design_drafted` | 3 |
| `defer_claim_specific_design_review` | 73 |
| `defer_global_old_roster_unverified` | 51 |
| `defer_group_roster_and_measure_review` | 9 |
| `existing_v2_duplicate` | 10 |

The 10 duplicate cases are the seven committed Heritage/WGI holdouts plus `trade_openness_consumer_welfare_1980_2024`, `education_quality_trade_openness`, and `food_market_liberalization_nutrition` in the committed nine-claim trade family. The 51 global-scope legacy rows give fitted-country counts but not fitted country rosters in compact diagnostics; this audit did not claim a geographic holdout from them. The 9 group-scope rows need historical group expansion. The remaining explicit-sample cases are queued for claim-specific design review, not declared impossible.

## Three preregistration candidates

Each candidate excludes **every country named in its old spec**, a conservative superset of the old fitted sample. The source-pinned preflight reads only `country_iso3` and `year` columns, restricts to the frozen ISO3 country list, joins exact t to t+1 calendar keys, and requires at least five paired key years per remaining country. A key can have an unusable value; these counts are upper bounds on the eventual complete-case sample, and passing the key envelope does not guarantee the registered minimum sample gate. All proposed claims are associational.

The word **holdout** is relative to each named old ID. These countries and WDI/WGI vintages can overlap the 16 WGI/trade v2 fits already in IESET; the Fraser growth endpoint is also related to an already fitted trade-family GDP-growth endpoint. This cohort is not globally unseen data. The three-test correction covers only these three registered primary tests, and no old or existing-v2 result is counted as fresh evidence here.

### Historical old-run country proof

The relevant old run is the diagnostics artifact committed at the revision below. At each revision, the old spec's country roster is identical to the roster printed in this audit, and that revision's `scripts/run_panel_fe.py` filters the panel to `sample.countries` before passing `panel_filt` into `run_panel_ols`. These checks use historical committed code, rather than the current runner. Therefore the old fitted set could not include a country outside the excluded roster.

| Old ID | Run-artifact commit | Historical filter / fit lines | Recorded fitted countries | Exact fitted-set evidence |
| --- | --- | --- | ---: | --- |
| `economic_freedom_index_income_correlation` | `5c77bbcf615b19ffc7dbc085d17a05255969ddd4` | 1545–1553 / 2116 / 2192 | 42 of 44 | The old diagnostics give a count but no row-level fitted roster, and the old manifest is absent. The historical 44-country filter proves the fitted set was a subset of the excluded 44. |
| `financial_market_depth_productivity` | `0265cebb33d0ef5e98fd44b09a59717a89003522` | 1492–1500 / 2063 / 2139 | 40 of 40 | The old diagnostics' country count equals the historical spec's 40-country filter, so the fitted set is exactly that roster. |
| `female_lfp_market_opportunity` | `f94eaa58c6579e3a48bdcca2c3db51099b1ea728` | 1683–1691 / 2321 / 2397 | 40 of 40 | The old diagnostics' country count equals the historical spec's 40-country filter, so the fitted set is exactly that roster. |

The economic-freedom exact 42-country set cannot be established from the preserved run packet. Excluding all 44 historical spec countries remains sufficient for country disjointness because the historical runner filtered to those 44 before fitting.

| Old ID | Old roster | Proposed primary endpoint | ≥5-year key pairs / countries, upper bound | Treatment years |
| --- | ---: | --- | ---: | --- |
| `economic_freedom_index_income_correlation` | 44 | exact t-to-t+1 log real GDP per capita (PPP) growth | 2,520 / 120 | 2000–2021 |
| `financial_market_depth_productivity` | 40 | next-year log TFP-index change | 2,720 / 136 | 1996–2018 |
| `female_lfp_market_opportunity` | 40 | next-year female labour-force participation | 4,008 / 167 | 1996–2022 |

The fixed complete-case gates are 1,500 pairs/70 countries, 1,000/50, and 2,500/100 respectively. Those gates are evaluated only after the shared first-addition preregistration commit; no outcome value, null status, positivity, or coefficient has been assessed by the current preflight.

### Candidate design and blockers

#### `economic_freedom_index_income_correlation`

- Old spec: `hypotheses/growth/economic_freedom_index_income_correlation.yaml`.
- Old-country exclusion: ARG AUS AUT BEL BRA CAN CHL CHN CZE DEU DNK EGY ESP EST FIN FRA GBR GHA HKG HUN IDN IND IRL ITA JPN KEN KOR MEX MYS NGA NLD NOR NZL PHL POL RUS SGP SWE THA TUR USA VEN VNM ZAF.
- Design: Fraser aggregate score at t predicts the exact t-to-t+1 log change in WDI real PPP GDP per capita, controlling for log population, trade share, and WGI rule of law at t, with country and year fixed effects and country-clustered uncertainty. All pinned files must pass hash custody before fitting. The legal-system and sound-money subindices are separately predeclared descriptive sensitivity analyses on their available subsets of the primary panel, with their own sample counts and no extra verdicts. Missing component rows do not filter primary rows, while a missing or mismatched pinned component file stops the entire run at the custody gate.
- Blocker/limit: The old draft produced PARTIAL from 924 observations / 42 countries; the old manifest and packet are missing. Heritage is excluded from this narrowed Fraser design because relevant-period usable coverage has not been established prospectively. The key-only envelope can shrink after complete-case and positive-log screens. Causality and the old stronger-subindex claim are not established.

#### `financial_market_depth_productivity`

- Old spec: `hypotheses/regulatory/financial_market_depth_productivity.yaml`.
- Old-country exclusion: ARG AUS BGD BRA CAN CHL CHN COL DEU DNK EGY ESP EST FIN FRA GBR IDN IND ITA JPN KEN KOR LKA MAR MEX MYS NGA NLD NOR NZL PAK PER PHL POL SWE THA TUR USA VNM ZAF.
- Design: WDI private credit to GDP at t predicts log(PWT TFP index at exact t+1) minus log(PWT TFP index at t), controlling for log WDI GDP per capita and WGI rule of law at t, with country and year fixed effects and country-clustered uncertainty.
- Blocker/limit: The old candidate was a proxy screen of next-year GDP growth, not TFP, with SUPPORTED verdict from 895 observations / 40 countries; the old manifest is missing. The new TFP endpoint is a revised measured estimand and must not inherit the old verdict or scoreboard link.

#### `female_lfp_market_opportunity`

- Old spec: `hypotheses/labour/female_lfp_market_opportunity.yaml`.
- Old-country exclusion: ARG AUS BGD BRA CAN CHL CHN COL DEU DNK EGY ESP EST FIN FRA GBR IDN IND ITA JPN KEN KOR LKA MAR MEX MYS NGA NLD NOR NZL PAK PER PHL POL SWE THA TUR USA VNM ZAF.
- Design: WDI services value-added share at t predicts WDI female labour-force participation at exact t+1, controlling for log real GDP per capita and WGI rule of law at t, with country and year fixed effects and country-clustered uncertainty.
- Blocker/limit: The old candidate had a SUPPORTED verdict from 986 observations / 40 countries, but its manifest and packet are missing. The new claim is limited to the measured services–participation association; “market opportunity” is not directly identified.

## Exact local source pins

The following paths and SHA-256 hashes were checked on this host. Raw vintages are ignored by Git; a later estimator must verify these hashes, and another host needs the same immutable files or a reproducible retrieval step. The Heritage source is listed as a source considered but excluded from the primary design.

**Fraser provenance limit:** `data/manifests/baseline_pull.yaml` lists the three Fraser series as requested inputs, but no fetch or derivation manifest for their narrow parquet slices was found. The local `aggregate_score` slice is byte-identical to the same-stamp `summary_index` slice. The repository Fraser fetcher describes a wider EFW panel, but does not establish that these slices came from its local workbook or panel. Upstream acquisition and component transformation are unverified beyond the pinned local paths and SHA-256 hashes. Each Fraser slice is marked `local_vintage_pinned_derivation_unverified` with `source_manifest: null` in prospective run provenance.

| Source role | Local path | SHA-256 |
| --- | --- | --- |
| credit | `data/vintages/world_bank_wdi/FS.AST.PRVT.GD.ZS@2026-05-05T194720Z.parquet` | `57d2717d9097b3142f9b116242218621e4560a6bf4e29ddc22081dd66b2a1b19` |
| efw | `data/vintages/fraser_efw/aggregate_score@2026-05-02T220000Z.parquet` | `9b9550678cf7dd6c17d1744a045512d74ee4d6f7c88a4c65aa389761d22cf76a` |
| female | `data/vintages/world_bank_wdi/SL.TLF.CACT.FE.ZS@2026-05-05T194807Z.parquet` | `c3b8ecd5c8a7ac7c1ab2fbf61675494c2f6a88093d3b64dfd808c542e96d1186` |
| gdpgrowth | `data/vintages/world_bank_wdi/NY.GDP.PCAP.KD.ZG@2026-05-05T194650Z.parquet` | `3bd65e60a77a1ad1cddeb9847cc579508c7e0f1c5e920c507b6953478f9604cf` |
| gdplevel | `data/vintages/world_bank_wdi/NY.GDP.PCAP.KD@2026-05-05T194645Z.parquet` | `0cf53ee3a334988ded027fbe160a8d8c70773656772daf1c82206eb3f7c02a9f` |
| gdpppp | `data/vintages/world_bank_wdi/NY.GDP.PCAP.PP.KD@2026-05-05T194648Z.parquet` | `6432d570bd5e7d94d659d310c48454caedb7b105db0bfeebbe1e44189c63ecfb` |
| heritage | `data/vintages/heritage_ief/overall@2026-05-02T220000Z.parquet` | `fd2f7b39804dc5ec284396098b8dbf55dbff63d771d4a20b66e7dbfd2f905a74` |
| legal | `data/vintages/fraser_efw/legal_system_property_rights@2026-05-02T220000Z.parquet` | `014580e715bac818d409ce8b88b7ad75684aaac5ae8a187a344ce1f721f39477` |
| population | `data/vintages/world_bank_wdi/SP.POP.TOTL@2026-05-05T194826Z.parquet` | `6e8ccda8b27d188d08e0fbf036828c975641453c12e6e68d5807657140cd9456` |
| rl | `data/vintages/wgi/RL.EST@2026-04-30T114245Z.parquet` | `63d71d06668ef8e8cff186d11bb9ca948e8ae82b857bf31e1cbb122ae847c91d` |
| services | `data/vintages/world_bank_wdi/NV.SRV.TOTL.ZS@2026-05-05T195011Z.parquet` | `3e4ecdf108553bd3449986ab0603ac062873ebc42bf40d2fa2c16dc52fc11fed` |
| sound | `data/vintages/fraser_efw/sound_money@2026-05-02T220000Z.parquet` | `ee48d086a9bb8d6d332d6df79eea95bed439d408b6f0a0e193a345212d93eb4d` |
| tfp | `data/vintages/pwt/rtfpna@2026-05-05T195242Z.parquet` | `c919c4e3f1e766651cdf4ef3e252b99164fd2dacd234be830d98879df1cf800a` |
| trade | `data/vintages/world_bank_wdi/NE.TRD.GNFS.ZS@2026-05-05T194657Z.parquet` | `4ecf502c1695a316e0d31dda4a90cb95d69494cf34cec26cee6f96420e4c34b1` |

## Registration and credit gate

1. Commit new IDs, exact source pins, steelmen, a fixed three-test family threshold, and the source-pinned runner before any held-out estimation.
2. The runner must verify that all three registrations, steelmen, and itself match both `HEAD` and their shared first-addition commit bytes, and that run artifacts were absent from that first-addition commit.
3. Fit only after that commit; keep the previous verdict disclosure, old-country exclusion, exact-year joins, complete-case gates, and all adverse/null findings.
4. Audit replication, source custody, estimator validity, corrections, second-order scope, and claim-level mapping before any public or scoreboard credit.
