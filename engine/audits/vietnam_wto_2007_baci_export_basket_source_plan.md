# Vietnam WTO 2007 BACI export basket — frozen source and test plan

This file, the hypothesis, steelman and runner must first appear in one commit before any selected BACI flow magnitude is read. `plan` reads no flow value. `extract` requires that preregistration commit, verifies the original ZIP byte hash, then writes a small attributed source slice. The slice and its manifest must be committed separately before `run` evaluates any flow. No substitution or window change is authorized after registration.

## Source and policy custody

- CEPII Gravity V202211 CSV ZIP: `https://www.cepii.fr/DATA_DOWNLOAD/gravity/data/Gravity_csv_V202211.zip`, member `Gravity_V202211.csv`, SHA-256 `7ffea0510a536587f2f9295bbafef4a312a36b366acc256eb6d9770fe35e44b1` (also recorded in `data/manifests/fetch_run_2026-05-15T175027Z.yaml`). The local ignored copy is `data/raw/cepii/Gravity_csv_V202211.zip`. CEPII's [Gravity documentation](https://www.cepii.fr/DATA_DOWNLOAD/gravity/doc/Gravity_documentation.pdf) describes its dyad-year series and Etalab Open Licence 2.0, permitting attributed reuse. The tracked slice and all result artifacts cite CEPII and the source vintage.
- [WTO Viet Nam accession timeline](https://www.wto.org/english/thewto_e/acc_e/a1_vietnam_e.htm): accession approved 7 November 2006, notification of acceptance 12 December 2006, membership 11 January 2007. Annual CEPII `wto_o` is a membership cross-check, not an estimate of tariff intensity.
- This case measures directed nominal BACI merchandise flows embedded in CEPII Gravity, not real export volume, TFP, tariff changes, welfare, or causal effects.

## Fixed grid and key-only feasibility

- Origins: VNM treated; THA, MYS, IDN, PHL fixed ASEAN donor origins. Destinations: USA, CAN, FRA, DEU, GBR, ITA, ESP, NLD, SWE. Years: every year 2002–2012. The expected grid has 5 × 9 × 11 = 495 unique existing-country directed dyad-years. `country_exists_o` and `country_exists_d` must both be 1; an extinct `DEU.1` duplicate is excluded, while an extra valid duplicate is fatal.
- The pre-commit key-only scan found 495 of 495 unique valid cells, a non-null `tradeflow_baci` field in each, `wto_o` equal to 0 for VNM in 2002–2006 and 1 for VNM in 2007–2012, `wto_o` equal to 1 for donors throughout, and `fta_wto` equal to 0 for all selected dyads throughout. It did **not** inspect the values, signs or magnitudes of any flow.
- Preperiod 2002–2005; exclude both 2006 (approval and acceptance) and 2007 (membership transition) from the contrast; postperiod 2008–2012. Every year remains required for integrity. No source replacement, imputation, winsorisation, donor/destination replacement or reverse direction.

## Estimand and gate

1. For each origin–destination–year, require one finite nonnegative BACI flow. Calculate `log1p(flow)`. For each origin-year, take the equal-weight arithmetic mean over the nine destination logs.
2. For each origin, compute the post-2008–2012 mean minus the pre-2002–2005 mean. The primary contrast is the VNM change minus the median of the four donor changes.
3. Before grading direction, require the absolute difference between VNM's preperiod OLS annual slope and the median of the four donor preperiod slopes to be at most 0.03 log units per year.
4. Compute four donor placebos: each donor's change minus the median change of the other three donors. SUPPORTED requires the primary contrast to be at least `ln(1.15)` and strictly above every placebo. REFUTED requires at most `-ln(1.15)` and strictly below every placebo. Other valid outcomes are PARTIAL. Any source/key/status/value/pretrend failure is INCONCLUSIVE. This rank check cannot yield a conventional significant p-value with only five origins.

This is **one** hypothesis, not 45 dyad hypotheses or nine destination hypotheses. The chosen destinations had no CEPII-coded FTA overlap and complete source keys. The case was selected from a key-only lead set: an earlier China WTO export claim already exists, Saudi Arabia's nominal exports are especially exposed to oil-price shocks and rapidly changing early BACI coverage, and Russia's 2014 sanctions leave only one clean post-accession year. The 2001 US–Viet Nam bilateral trade agreement and 2008–2009 global crisis remain important confounds. Earlier CEPII FTA calibrations produced six pretrend failures among seven events, which provides no favorable prior outcome information for this separate WTO case. No causal, policy-score, featured or school credit is available.
