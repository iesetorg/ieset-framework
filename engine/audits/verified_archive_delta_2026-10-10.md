# Verified archive delta: 14 frozen failures after the 632-record checkpoint

Date: 2026-10-10. Review base: isolated integration commit `53d733aa3640192d351323179f125e5790f735c0`. This audit reads the saved registrations, source locks, diagnostics, and the regenerated conversion funnel in the integration checkout. It changes no hypothesis, result, verdict, source, gate, or tier.

## Census and decision

The preceding committed checkpoint had 632 public records / 2,226 hypotheses and 273 verified archives. Three subsequently merged, separately registered eight-test families added 24 hypotheses: ten public descriptive calibrations (two GFDD, eight FAOSTAT) and **14 verified archives** (six GFDD, eight WDI resource-rent). The regenerated local funnel reports **642 public / 2,250 total, 287 verified archives**, and 112 first-action `data_or_design_rerun` cases (98 prior plus these 14). The target of 872 public records still has a gap of 230 at this checkpoint.

**No same-ID graduation in these 14 is justified.** Every new archive has a canonical `INCONCLUSIVE` verdict and a prespecified sample, event, or influence gate failure before an eligible primary result. No threshold, roster, source vintage, or outcome can be changed after measurement to turn its diagnostic into a public calibration. The previous 273 verified archives were assessed in `verified_archive_98_data_design_no_go_2026-10-10.md`, `verified_estimator_nonplaceholder_screen_2026-10-10.md`, `verified_archive_wave2_2026-10-10.md`, and their cited case-specific reviews. The 24 newly introduced hypothesis/run paths are additions; no pre-existing hypothesis/run path changed between the 632-record checkpoint and this review base.

## Six GFDD banking-crisis tests

These use the same frozen 2000/2005/2010 anchor family and future recorded crisis-spell onset. The eight-test registration was committed as `55b8dbb`; distinct source locks preceded the result commit `3b369628552e94239fa63fa02e9b2e181f9365ab`. The two other family members, bank Z-score and bank credit/deposits, passed gates and are public PARTIAL calibrations. The following six remain archived:

| Indicator ID suffix | Valid rows / countries | Future onset windows / countries | Frozen stop |
| --- | ---: | ---: | --- |
| `nonperforming_loans` | 123 / 49 | 8 / 8 | country and onset-window floors |
| `capital_assets` | 111 / 46 | 6 / 6 | row, country, onset-window and onset-country floors |
| `regulatory_capital` | 128 / 50 | 8 / 8 | onset-window floor |
| `liquid_assets` | 233 / 86 | 10 / 10 | top-country predictor concentration |
| `loan_loss_provisions` | 105 / 44 | 6 / 6 | row, country, onset-window and onset-country floors |
| `cost_income` | 216 / 81 | 10 / 10 | top-one-percent and top-country predictor concentration |

Full IDs append `_future_banking_crisis_2026` to the suffix with the `gfdd_` prefix, as recorded in `engine/runs/<id>/diagnostics.json`. Ten or fewer recorded onset windows in most cells are thin evidence even where the fixed floor is met. The local GFDD parquet hashes are pinned, but its original download transaction has no tracked fetch manifest and component-source redistribution rights have not been established; that custody limit is separate from these frozen failures. See `gfdd_bank_resilience_crisis_results_2026-10-10.md` and its post-result clarification.

## Eight WDI resource-rent / sector-growth tests

The eight `wdi_{gas,mineral,oil,total}_rent_{manufacturing,services}_growth_2026` IDs share the four-rent by two-sector family registered as `732382e`, source-locked separately, and measured as `bd0f52b`. All eight have 495–509 valid paired-sector windows across 141–146 countries, passing coverage floors. In each cell, the largest one percent of residualized rent observations supplies **39.4%–61.2%** of rent variation, exceeding the frozen **35%** cap. The six gas/mineral/oil cells also exceed the **25%** top-country rent cap. No eligible primary coefficient was fitted. Exact per-cell diagnostics and source-custody limits are in `wdi_resource_rents_sector_growth_no_go_2026-10-10.md` and each run packet.

## Best next work, without retroactive graduation

1. **Declared missing observations:** acquire a verifiable annual Canada broad-money-growth series for the 2019–2024 Anglo claim, and claim-matched protected-land 2005/2015 plus food-production 2023 endpoints for a two-record future family. The existing exact-hash and endpoint contracts still govern the old IDs. A changed source or estimand requires a new registration and independent holdout; the observed availability here grants zero conversions.
2. **Source custody and design:** locate the original Doing Business insolvency release and transaction record before considering the archived bankruptcy-law question. Its current converted Parquet and one shared 2007–08 crisis cohort do not establish a comparable multi-event design. Fix treatment identity, event clock, method regimes, and holdout prospectively.
3. **New prospective family selection:** prefer a distinct mechanism and measured outcome with a source-key roster and family denominator fixed before selected values. The 1,320 same-commit legacy pairs cannot become strict preregistrations by metadata edits, and the 131 Fraser/GDP-per-person placeholders do not measure their varied claims. Subgroup proliferation would inflate record counts without independent questions.

Reproduction: compare `engine/audits/hypothesis_conversion_funnel_2026-10-10.json` at the 632-record checkpoint with the regenerated integration copy; inspect the fourteen `engine/runs/<id>/diagnostics.json` records, the two dated family result reviews, and `git diff --name-status` for `hypotheses/` and `engine/runs/` from `0876e906fa87aa8465b8b029bb2f8fdbf30131f3` to the review base. This is a local evidence audit, not a public deployment or a claim that future data cannot yield a valid test.
