# SIPRI military burden and later UNDP components — results

Registration `b1322821a8d91ddf7bda243362a7f62f75599bb7`; source lock `ff18acad92a6d61fde3c401030295396b174ccbd`. All four cells remain in the Bonferroni denominator.

| Cell | Verdict | Rows | Countries | Gate summary |
| --- | --- | ---: | ---: | --- |
| `sipri_military_burden_later_life_expectancy_2026` | PARTIAL | 3075 | 155 | estimable association does not clear directional magnitude and multiplicity gates |
| `sipri_military_burden_later_mean_schooling_2026` | PARTIAL | 2971 | 153 | estimable association does not clear directional magnitude and multiplicity gates |
| `sipri_military_burden_later_expected_schooling_2026` | PARTIAL | 3036 | 154 | estimable association does not clear directional magnitude and multiplicity gates |
| `sipri_military_burden_later_gni_per_capita_2026` | PARTIAL | 3064 | 154 | estimable association does not clear directional magnitude and multiplicity gates |

These are correlated, overlapping-window associations; they are not four independent replications. The military share can move because of the GDP denominator and security or war shocks, which may independently change every outcome. This does not identify a spending tradeoff or policy effect. SIPRI figures can be revised, and the local extract has no cell-quality flags. Zero causal, policy, school, position or featured credit.
The exact local SIPRI and UNDP Parquet hashes match tracked fetch manifests. Raw SIPRI measurements are not copied into Git. See the preregistration for source URLs and the frozen failure rules.

Source-unit repair: The pinned SIPRI Share-of-GDP Parquet stores fractions, while the frozen test expresses military-share changes in percentage points. The first locked unscaled execution stopped at the material-exposure gate in all four cells; no coefficient was estimated. A separate pre-coefficient adapter multiplies SIPRI inputs by exactly 100. The original no-fit diagnostic is preserved, and no registered threshold, roster or model changed. This is a disclosed post-gate physical-unit correction.

A serialization-only amendment followed the preliminary corrected fit: final diagnostic SHA-256 fields and replay commands were added to all four packets. Frozen numeric outputs, sample gates and verdicts match the committed preliminary-fit audit exactly.
