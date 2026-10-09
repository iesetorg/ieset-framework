# Eight verified archived records with no canonical result — 2026-10-09

This review covers the eight IDs in `hypothesis_conversion_funnel_2026-10-09.json` under `missing_result_rerun`. It inspected frozen YAML, old run cards/diagnostics, source manifests, runner code, and source **key columns only**. It did not read outcome or treatment magnitudes, fit a model, overwrite a run, or change a verdict. None is ready for an honest conversion today.

## Five BIS private-investment screens

All five stored results say `INCONCLUSIVE_DATA_PENDING`; the country gate is part of the frozen decision, even where a coefficient looks decisive. Their common WDI private-investment outcome is `NE.GDI.FPRV.ZS@2026-04-30T115003Z.parquet`, pinned at SHA-256 `84294f869d513ae4c70154630b31388a53b41c42bf849a006740c9324ebeba14`. No later local vintage of that outcome was found. The source fetch manifest is `data/manifests/fetch_run_bootstrap_2026-04-30T121833Z.yaml`.

| Frozen ID | Stored usable coverage | Registered minimum | Additional blocker |
| --- | ---: | ---: | --- |
| `bis_corporate_credit_boom_investment_slowdown_panel_1970_2025` | 2,607 rows; 14 countries | 600 rows; 20 countries | `credit_gdp_growth_5y` is continuous, but the historical runner computes its raw contrast by grouping exact treatment values `0` and `1`; no meaningful binary exposure threshold was registered. Its six “treated” rows are exact `1` values, not a defined boom group. |
| `bis_corporate_dsr_investment_slowdown_panel_1999_2025` | 364 rows; 2 countries | 450 rows; 15 countries | Fails both sample gates. |
| `bis_credit_gap_private_investment_reversal_panel` | 3,147 rows; 14 countries | 600 rows; 20 countries | Fails country gate. |
| `bis_credit_gap_private_investment_slowdown_panel_1970_2025` | 3,147 rows; 14 countries | 700 rows; 20 countries | Fails country gate; duplicates the reversal screen's exposure/outcome with a different registered sample floor. |
| `bis_reer_volatility_investment_drag_panel_1964_2026` | 2,349 rows; 14 countries | 900 rows; 20 countries | Fails country gate. |

Key-only comparison of the May and July BIS vintages found **no new country keys** in the required slices: credit gap `CG_DTYPE=C` had 44 countries in each (44 new quarterly country-period keys); corporate DSR `DSR_BORROWERS=N` had 17 in each (17 new quarterly keys); REER monthly real broad basket had 64 in each (192 new monthly keys). This does not prove that complete-case coverage is unchanged, because it does not inspect value validity. It provides no basis to relax a gate or predict that the six or thirteen additional complete countries needed will appear in a rerun. The newer BIS fetch manifests are `fetch_run_2026-07-22T141212Z.yaml` and `fetch_run_2026-07-23T151632Z.yaml`.

## Three OECD Productivity Database screens

The three old runs have coefficients and source hashes, but each records `REFUTED_OR_WEAK` as its status. The frozen rule says support requires the expected sign at p<0.10 and calls the remainder “partial or weak” without an exact split or a canonical `PARTIAL`/`REFUTED` rule. A new label chosen from the observed result would be an after-result rule change.

| Frozen ID | Stored status | Exact blocker |
| --- | --- | --- |
| `oecd_pdb_market_reform_productivity_compounder` | `REFUTED_OR_WEAK` | No registered non-support verdict boundary; the 2018–2023 PMR exposure also overlaps the named 2018–2024 productivity window, so the claimed “following window” needs a new temporal design. |
| `oecd_pdb_public_sector_share_productivity_drag` | `REFUTED_OR_WEAK` | No registered non-support verdict boundary. |
| `oecd_pdb_tfp_growth_frontier_persistence_1970_2025` | `REFUTED_OR_WEAK` | No registered non-support verdict boundary. |

The local OECD PDB file used by these runs matches the SHA-256 pinned in their run manifests (`3546c5c773a15933c439a9975bb6436c13f2df1ae250c75419340c2c91032b5c`). A matching fetch-time manifest for this exact 2026-05-12 PDB file was not found in `data/manifests`; the run-level hash establishes local replay identity, not complete upstream fetch custody.

## Disposition

- Keep all eight archived. `INCONCLUSIVE_DATA_PENDING` remains honest for the five BIS runs; `REFUTED_OR_WEAK` remains an ungraded historical status for the three OECD runs.
- A future BIS rerun needs source-custodied new outcome coverage and a key-only preflight before reading values. It must preserve the frozen country and observation floors. The continuous credit-boom contrast also needs a separately registered v2 decision rule.
- The OECD tests need prospectively versioned rules that specify support, partial, refutation, and missing-data cases before another fit. The PMR test also needs a nonoverlapping outcome window if it is to test later productivity.

No source fit or graduation was attempted in this review.
