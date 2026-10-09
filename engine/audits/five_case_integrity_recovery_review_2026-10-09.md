# Five-case verified-archive integrity recovery review — 2026-10-09

Scope: the three `integrity_reconcile_and_rerun` and two
`prospective_rule_version_required` entries in
`engine/audits/hypothesis_conversion_funnel_2026-10-09.json`. This is a
read-only decision review. It changes no registration, run, verdict, public
tier, or school score. Existing result values cited below were already
published in their run packets; no new candidate outcome was inspected.

| Hypothesis | Frozen rule and source custody | Why the old run cannot graduate now | Recovery boundary |
| --- | --- | --- | --- |
| `oecd_epl_growth_shock_unemployment_persistence_panel` | The registered support rule requires **both** a positive interaction coefficient of at least 0.25 at p≤0.10 and a raw high-minus-low contrast of at least 0.25, with 350 observations and 20 countries. Its manifest pins OECD EPL and WDI unemployment/GDP vintages. | The runner formed a binary `high_epl_x_negative_growth` treatment, then selected the top quartile using `>=` the 75th percentile. The stored raw contrast is null because this selected only a high group; the earlier `REFUTED` label counted the undefined contrast as failed. A nonsignificant coefficient alone cannot supply the missing raw decision. | Keep quarantine. A new-ID test must state how ties and zero/one treatment values define both raw groups, fix the shock and forward-unemployment windows, and register a genuinely unused temporal or geographic holdout before reading its outcome values. A replay of the old verdict is not a repair. |
| `oecd_pdb_hours_reduction_output_tradeoff_panel` | The frozen model is `gva_growth ~ hours_growth + C(country) + C(year)` with country clustering on the SHA-pinned OECD PDB vintage. The runner's `not_negative_large` support gate is lower 95% CI > −0.5 on the *hours-growth* coefficient. | The published coefficient is positive (+0.2197, 95% CI +0.106 to +0.333). Under the model, a reduction in hours growth predicts a reduction in GVA growth, contrary to the English no-output-loss claim. The frozen support gate tests the opposite direction and cannot be reinterpreted after seeing the estimate. | Keep quarantine. A new-ID equivalence or noninferiority design needs the correctly signed estimand, a justified margin, a fixed independent holdout, and a precision gate. It must not treat a nonsignificant adverse coefficient as proof of no tradeoff. |
| `pcw100_us_mw_bite_ratio_p10_wage` | The registered screen uses state/year fixed effects and state clustering; its treatment is USDOL minimum wage divided by **BLS median** hourly wage, and its outcome is log **BLS tenth-percentile** hourly wage. Derived panels and their upstream source files have pinned manifests. | The September audit quarantined this run as a “mechanical identity” and called overlapping state names in top/bottom quartiles a pipeline bug. The code does **not** establish either literal finding: p10 is not the treatment denominator, and quartiles are selected on **state-year rows** before unique state names are listed. A state can move between quartiles over time; with distinct q25 and q75 cutoffs, one row cannot be in both. Full-model R²=0.975 includes state/year effects and does not by itself demonstrate an identity. The contemporaneous wage denominator, legally binding floor, and source-family coupling still limit inference; the original 17 school mappings should not be restored by a purely textual correction. | Correct the two overstatements in the adversarial audit only after independent review. Verify row keys and row-level contrast membership without outcome fitting; replay the original SHA-pinned run read-only; inspect whether p10 equals the legal floor in the relevant rows and whether the outcome/treatment construction has further leakage. If those checks pass, consider a **calibration-only** descriptive rescope with no causal or automatic school-score credit. A causal wage-effect test needs a new-ID event design and independent outcome window. |
| `argentina_milei_disinflation_monetary_reconfiguration_2023_2028` | The preregistered six metrics and 4-of-6 support count use INDEC and BCRA source files pinned in the derived-panel manifest. The spec has no `falsification.rule`; its English claim also requires no “reversal markers,” which it never defines operationally. | The stored `SUPPORTED` packet has observed CPI only through July 2026 and BCRA data only through August 2026 for an end-2026 durability claim. It marks two money-growth streaks `NOT_MET` before their December 2026 deadline and counts four other metrics as met. The remaining months and undefined reversal test prevent a final registered verdict, regardless of the current count. | Keep archived. A new-ID rule must define reversal markers, fixed endpoint and missing-month behavior before any new outcome is read. The end-2026 window cannot be declared complete in October 2026. Previously inspected 2026 values must be disclosed and any later independent holdout credited only as lower-tier calibration. |
| `el_salvador_bukele_security_growth_equilibrium_2019_2026` | The six-metric 4-of-6 case uses a fixed eight-country WDI peer set and SHA-pinned derived panel; it also lacks a `falsification.rule` and an operational reversal-marker definition. | The stored homicide durability metric is `MET` on 2022 alone although its declared window runs through 2024 and the local 2023–24 homicide cells are null. Counting that as complete supplies one of the four claimed hits. A 2022 observation cannot prove the registered 2022–24 durability condition. | Keep archived. First land a source-custodied, definition-compatible 2023–24 homicide series, then register a new-ID complete-data and reversal-marker rule before reading those candidate values. If the years are already known to the researcher, disclose that and cap evidence accordingly. |

## Minimum-wage structural check

The existing registered analysis frame has 459 unique state-year rows. Its
stored bottom and top quartile cutoffs are 0.409143 and 0.505079, with 115
rows in each group. The state-year intersection is **zero**. Five state names
occur in both display lists because their observations belong to different
years. Both derived-panel file hashes match their run-manifest SHA-256 entries.
A read-only join to the two SHA-pinned derived panels found only **2 of
115** top-quartile rows with p10 hourly wage within 1% of the effective
minimum wage, and **24 of 115** within 5%; none had a p10 wage below the
floor. The median-wage denominator was within 1% of p10 in **0 of 115** rows.
This refutes the literal identity and overlapping-row claims in the September
audit. It does not establish a causal wage effect or settle contemporaneous
endogeneity. No model was refit in this review.

## Decision

No case supplies an immediately defensible additional public graduation from its
stored packet. The minimum-wage audit contains two correctable overstatements,
but correcting prose is not a substitute for the row-level/source replay and a
separate decision on school-score links. The other four need new registered
decisions or unobserved data. Do not remove a quarantine, copy an old
`SUPPORTED`/`REFUTED` label into a new run, or count a proposed design as a
graduation.
