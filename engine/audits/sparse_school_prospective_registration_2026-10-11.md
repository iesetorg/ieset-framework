# Sparse-school prospective registration — 2026-10-11

This first batch adds **two new directional, school-specific hypotheses** before any selected outcome or run exists. It adds one linked claim to Social Democratic and one to Degrowth; New Keynesian remains a source blocker. **Current public, tested, and directional scored counts increase by zero.** These are descriptive forecasts, not causal evaluations or policy-effect evidence. The school predictions and claim links are frozen now; any future public school credit still requires the ordinary registration, source, estimator, replication, integrity, and evidence-tier gates.

| School | New ID | Forecast and primary estimate | Source and future holdout | Current score |
| --- | --- | --- | --- | ---: |
| `social_democratic` | `nordic_cash_redistribution_gini_2027_2029_forward` | Equal-country mean of the 2027–2029 market-minus-disposable OECD IDD Gini in DNK, FIN, ISL, NOR, SWE. Support ≥0.10; refute <0.07. | First IDD release available on/after 2032-01-01; all 15 exact pairs or INCONCLUSIVE. | 0 |
| `degrowth` | `world_material_footprint_per_capita_decoupling_2026_2029_forward` | World 2026→2029 material-footprint-per-person percentage change conditional on real GDP-per-person growth ≥6%. Refute if footprint falls ≥5%; otherwise support. | First OWID material-footprint and WDI GDP-per-person releases available on/after 2034-01-01; exact World endpoints or INCONCLUSIVE. | 0 |

## Source custody and interpretation

The OECD [Income Distribution Database](https://www.oecd.org/en/data/datasets/income-and-wealth-distribution-database.html) supplies market-income (`INC_MRKT_GINI`) and disposable-income (`INC_DISP_GINI`) Ginis under its `DSD_WISE_IDD@DF_IDD` dataflow. The same definition, year, age, scale, and methodology selectors must be paired. The difference describes measured cash-tax/transfer redistribution; it is not a reform counterfactual, does not include in-kind services or indirect taxes, and cannot alone identify welfare or growth effects.

The [OWID material-footprint-per-capita chart](https://ourworldindata.org/grapher/material-footprint-per-capita) currently exposes a UNEP/UN SDG consumption-based series through 2022; the [UN metadata](https://unstats.un.org/sdgs/metadata/files/Metadata-12-02-01.pdf) defines its raw-material-equivalent concept. The registered forecast uses its future World `OWID_WRL` row and [WDI real GDP per capita](https://data.worldbank.org/indicator/NY.GDP.PCAP.KD) World `WLD` row. It tests per-capita material decoupling in one window, not total extraction, ecological harm, or the merits of degrowth policy. The selected future footprint values do not exist in the current chart, while the checked local WDI vintage ends in 2025; neither registered endpoint was opened.

For both tests, the first qualifying future publisher snapshot must be preserved with raw response, source URL, license, fetch UTC, series metadata, manifest, and SHA-256 **before** reading selected values or creating a run. A later result cannot choose a different year, release, country, proxy, threshold, or model because an outcome is unfavorable. Source delays or definition changes are INCONCLUSIVE under the frozen rules. These claims belong to separate one-test families; they are not independent evidence for one shared mechanism.

## New Keynesian source blocker

No New Keynesian claim is added in this batch. The existing `fiscal_multipliers_zlb_higher_than_normal_regime` draft names a state-dependent quarterly fiscal multiplier but does not hold an OECD-wide, source-custodied exogenous fiscal-shock instrument, government-consumption series, matched real-output and rate series, and exact regime/normal-period roster. Its US defense-news instrument is not a ready OECD-country instrument. The existing `inflation_expectations_anchoring_flattens_phillips_curve` draft has a stub falsification rule, unresolved pre-2003 expectations, inconsistent country-specific price and unemployment-gap sources, and no fixed comparable NAIRU/output-gap vintage. Neither draft is a valid template for a newly scored school claim.

To register a New Keynesian successor, first choose **one** mechanism, obtain its publisher raw files and licenses, pin a common geography/frequency and an untouched future or independent holdout, specify the shock or expectations measure and primary estimand, and fix a directional threshold plus estimator-quality gates before any selected outcome inspection. A new ID is required; neither draft's saved result or broad school link can be relabelled.

## Required chronology

1. Commit the two hypothesis YAMLs, steelmen, reciprocal position claims, and this registration note with **no run directory or outcome slice**.
2. When the future release is available, verify exact source identity and roster, then commit a source lock and manifest separately before reading selected values.
3. Implement only the frozen primary calculation, retain INCONCLUSIVE and contrary outcomes, and replay from pinned bytes. Rebuild the evidence-tier and school-coverage audits before any public score change.
