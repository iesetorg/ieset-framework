# Verified archive source recheck: no same-ID graduation

Date: 2026-10-10. Read-only case review on the clean integration checkpoint
`cc84016f6d11de3d305937353030690de2cf49ae`. The ignored source files
mentioned below were inspected in `<LOCAL_HOME>/IESET` without changing that
checkout. This review changes no hypothesis specification, runner, result,
verdict, evidence tier, or frozen threshold. **Public delta: zero.**

The current conversion funnel still puts 155 verified archived records in
`estimator_repair_and_rerun`. The prior
`verified_estimator_nonplaceholder_screen_2026-10-10.md` identified 131
Fraser-index/GDP-per-person placeholder fits and 24 other records. Of those 24,
16 saved runs declare missing inputs and eight fail the complete registered
estimator or decision despite no saved missing-input flag. The separate
`verified_archive_nine_case_triage_2026-10-10.md` covers eight missing
canonical verdicts and the one apparent replication-only blocker.

## What newer local files actually unlock

| Frozen case | Present source evidence | Remaining registered-test blocker |
| --- | --- | --- |
| `labour_flexibility_security_complement` | The newer OECD EPL file has 1,355 rows in 1985–2025, but its sole indicator is `EPR_V1` (regular-contract protection), not the specified overall EPL measure. OECD TUD has trade-union density. OECD SOCX has an explicit `Active labour market programmes` spending category. | The original specification names OECD `OECD.ELS.SAE` for ALMP **and** unemployment-insurance net replacement rates. SOCX spending is not a replacement rate; no exact replacement-rate vintage was found. The old fit omitted EPL and density and never estimated flexibility × ALMP/UI for both employment and productivity. Substituting newly chosen OECD flows and a post-result interaction is not a same-ID replay of that packet. |
| `judicial_independence_growth_persistence` | The local V-Dem full vintage has both `v2x_jucon` and `v2xcl_rol`. | The available derived Fraser panel has `area_2_legal_system_property_rights`, not the frozen `legal_integrity` subindicator; the saved run substituted a generic reform exposure and fitted none of the judicial composite, interaction, 10-year post-reform outcomes, tercile volatility gap, low-judiciary marginal effect, event study, or exclusions. The spec's alternative “known structural reforms” are examples, not a closed event roster. Selecting events and a replacement Fraser field now would change the frozen test. |
| `wto_accession_productivity_spillover_panel` | Local WITS import-value years and a PMR `BARRIER_ENTRY` file exist. | `BARRIER_ENTRY` is not the registered `ETCR` series, and that PMR file has only 105 rows at **2018 and 2023**. It cannot give the 5-year pre-accession mean and concurrent barrier change for 1995–2020 accession events. No weighted foreign-tariff-faced measure is present. The old TWFE fallback is rank deficient and is not the registered Callaway–Sant'Anna group-time design with t−5 to t+10 dynamics, pretrend test, entry-barrier interaction, and ex-China check. |
| `demo_japan_ageing_deflation_link` | WDI CPI and old-age dependency data are present. | The first registration at `0c8fdfcd4da5ca90bed1cb02d70fd099b4ddccdd` requires `fred:JPNM2MB` and `imf:WEO.NGAP_NPGDP`; neither local vintage is present. The current YAML replaces the IMF gap with OECD OutputGap, which is not the frozen source. The saved panel FE fit is not a Johansen VECM or the 12-country comparator-rank test. |

These are the four clearest partial-source leads among the 16 missing-input
cases. The other twelve still have the specific missing declared sources and/or
full-test gaps listed in `verified_estimator_nonplaceholder_screen_2026-10-10.md`.
The eight non-missing-flag cases in that audit still lack an identified complete
frozen model; the Peru source-pinned draft was already rejected as a post-result
linear-trend choice, and privatisation has zero within-country treatment changes
under the registered WGI control window. The absence of a `variables_missing`
diagnostic is not positive evidence for graduation.

## Missing verdicts and replication path

The five BIS results in the nine-case triage remain below their frozen country
floors (14 versus 20, or 2 versus 15), even where a coefficient is significant.
The three OECD Productivity Database results still carry a combined
`REFUTED_OR_WEAK` status without a registered non-support split; assigning
`PARTIAL` or `REFUTED` after reading the fit would be a rule change. The tariff
case's historical fit uses current tariff **level**, while its registered
treatment is cumulative years above 15%; it also omits the registered real
household-consumption growth endpoint. The existing BIS exact-replay wrappers
repair paths only and do not manufacture canonical verdicts. All nine stay
archived.

## Reproduction and disposition

The first-registration source checks use `engine/preregistration_index.json`
and the historical spec commits. Source availability was checked from file
names and Parquet schema/key or dimension fields, without fitting models or
reading selected outcome/treatment magnitudes. Relevant local source files:

- `data/vintages/oecd/OECD.ELS.EMP_DSD_EPL_OV_DF_EPL_OV_1.0@2026-07-23T154113Z.parquet`
- `data/vintages/oecd/TUD@2026-05-05T195705Z.parquet`
- `data/vintages/oecd/DSD_SOCX_DF_SOCX_AGG@2026-05-05T210247Z.parquet`
- `data/vintages/vdem/vdem_cy_full@2026-05-05T200021Z.parquet`
- `data/vintages/fraser_efw/efw_panel@2026-05-02T202914Z.parquet`
- `data/vintages/oecd_pmr/BARRIER_ENTRY@2026-05-02T220000Z.parquet`
- `data/vintages/wits/import_value@2026-05-19T095253Z.parquet`

A source-custodied **new-ID** registration is the next honest route for a
redesigned question. A same-ID conversion would require an exact, claim-matched
rerun against the original rule, including every outcome and robustness gate;
this checkpoint supplies none. No old result or metadata should be promoted
from this recheck.
