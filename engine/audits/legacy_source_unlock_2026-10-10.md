# Legacy source unlock audit — 10 October 2026

Snapshot: `3ce5d151875db2e63b521664c06941f169432aab` on an isolated
worktree. This is a bounded source-key and claim-match audit, not a new
registration, run, or graduation. It did not open selected outcome magnitudes,
outcome null masks, or model estimates for a prospective test. Historical
result cards and old specification text were inspected only to identify
duplicate questions and known result exposure.

## What the added raw years actually unlock

The existing [legacy archive readiness audit](legacy_archive_v2_readiness_2026-10-10.md)
counts 1,320 same-commit registrations: 556 without a run manifest and only
203 with fully pinned source vintages. Among the latter it found 22 cases with
any extra raw calendar year. I independently screened the subset whose
manifest uses the `vintage_file`/`sha256` mapping shape and whose old and newer
raw files both survive on this host. This narrower parser covers 178 fully
pinned legacy cases. Reading only Parquet time keys finds **19 old IDs and 21
source pairs** with any added calendar year. The 19 is a subset of the earlier
22, not a revised total for all manifest shapes.

| Added key | Old IDs in this narrower screen | Claim-match assessment |
| --- | ---: | --- |
| BIS real residential property-price `WS_SPP`, 2026-Q1 after 2025-Q4 | 13 | One quarter cannot fill the old eight- or twelve-quarter forward-price horizons. Several other old claims use property prices as one channel in a wider conjunction. A new one-quarter predictive claim would be a different estimand and need its own registration and sample floor. |
| OECD labour-force `DSD_LFS_DF_LFS_INDIC`, 2025 | 5 | The youth-wage case has only four 2025 wage countries; the bargaining cases have no matching 2025 bargaining treatment; the union-density/Gini case has no matching 2025 Gini outcome; the Poland retirement case lacks the specified early-pension take-up measure. |
| OECD housing/well-being `DF_HSG_INEQ`, 2026 | 1 | This is a housing channel in the intergenerational-mobility claim, not a new mobility outcome or a full set of institutional channels. |
| ECB deposit-facility rate, 2026 | 1 | The negative-rates claim names the 2014–2022 episode. A 2026 rate observation cannot extend that historical treatment episode. |

The rows overlap: `intergenerational_mobility_cross_country` is in both the
BIS and OECD housing rows, so 13 + 5 + 1 + 1 source leads represent 19 IDs.
The BIS property file's latest period is 2026-Q1; the preceding version ends
2025-Q4. The BIS corporate debt-service file adds only 2025-Q4 to an existing
2025 calendar year. Its non-financial-corporation series has 17 country codes,
all inside the old `bis_corporate_dsr_manufacturing_drag_panel` roster, leaving
no country-disjoint corporate-DSR sample in this local source.

## Additional source-pair checks

The 67-group screen of the 820 legacy cases beyond the first review queue is
an upper bound on possible *design reviews*, not on graduations. Only 22 groups
in that dated screen lack its `screening_or_proxy_design` warning; all 67 lack
old evidence packets and manifests and require full design review. Several
promising direct pairs have since received distinct v2 tests: private credit
and manufacturing share, trade openness and growth, Fraser freedom and forward
income, remittances and participation, OECD working hours and employment, and
nominal EER × trade openness and inflation. Reusing their old source signature
or changing a geography label would not create an independent conversion.

Two additional direct pairs were checked against raw keys:

- The Eurostat industrial-power-price/unemployment and real-manufacturing-GVA
  files already had 2025 keys in the earlier local vintages; the July vintages
  add no new calendar year for those outcomes.
- The OECD combined statutory corporate-tax-rate files both end in 2024. The
  old 2000–2021 tax-competition spec itself described the post-2021 flattening
  or reversal. A retrospective 2022–2024 trend is not an unseen holdout.

## Decision for this lane

**Zero additional public records are established by this audit.** It is not
defensible to turn the old same-commit results public through a metadata edit
or a nominal new ID. The next measurable candidates need direct new source
coverage at the claimed horizon or an explicitly independent, claim-matched
country sample frozen before values are read. In particular, official
household disposable-income, pension-asset and household-saving, and
investment-financing decomposition vintages address specific old claims that
the current local files can only proxy. Every v2 still needs a committed
source-pinned specification, a separate result commit, exact replay, estimator
floors, and the public evidence audit. This lane gives no policy, causal,
school, featured, or count credit.
