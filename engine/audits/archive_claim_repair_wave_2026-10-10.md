# Archived claim repair wave: one disjoint-country conversion

Date: 2026-10-10. Isolated branch `codex/ieset-archive-claim-repair`, based on the consolidated evidence branch at `24d646693b4714a20be2cf9ab087d16e49b53cbe`. This review sought honest conversions from the archived corpus. **It does not relabel an old archived result.** The one public addition is a new, source-locked test of the narrow rule-of-law/corruption association; it earns calibration visibility only. The old `economic_freedom_corruption_decline` run remains archived as `legacy_same_commit`.

## Frozen sequence and result

| Boundary | Evidence |
| --- | --- |
| Registration before selected outcome access | `c3ad46dfac3bbb58aa30696e81cbbd50f4ff2786` fixed 132 V-Dem/WDI country codes, excluding every country in the old 40-country run; predictor years 1996–2022 and exact following-year outcomes 1997–2023; min 1,500 pairs/80 countries/15 pairs per country; max 12% country share of residualized treatment variation; two-sided p≤0.005; and three named robustness outcomes. The roster used country/year keys only. |
| Source custody | `d6d622d961589258c3da1a819dc3f21e05959fbb` recorded the original May 5 fetch manifest and SHA-256 pins for V-Dem `vdem_cy_full` (`89afa79f…`) and WDI real GDP per person (`0cf53ee3…`), without selected values or null masks. Raw sources stay ignored and local. |
| Estimator fixed before the run | `23a6f0b3d107b898278cfbe64dc389b4c29f1065` committed the country/year fixed-effects, country-clustered runner and exact-replay wrapper. No replacement source or post-result model branch is selected. |
| Result | `c52e0284ea858dfbb13df2dd94a11e3205e52172` saved `SUPPORTED`: 3,450 lagged pairs, 129 countries, primary coefficient +0.379091, country-clustered p=0.000004992, maximum country treatment share 10.434% (<12%), and three of three positive robustness coefficients. All registered gates passed. |

The test measures a *following-year within-country association* in a disjoint country pool. V-Dem rule-of-law and corruption indices share an expert-coded source family, and reverse causation/common reform can explain the pattern. It is not an economic-freedom policy effect, a causal estimate, or a school/position/featured claim. The packet sets school and policy score eligibility and credit to zero.

Exact replay passed. An independently fitted ordinary least-squares model with explicit country and year dummies and country-clustered uncertainty returned the same +0.379091 coefficient (SE 0.083215, p=0.000005224); the selected roster has zero overlap with the original 40 countries. The independent check is a second estimator implementation on the frozen sample, not a second dataset. `check_preregistration.py` with a temporary index verified 823 strict pairs, 1,320 legacy same-commit pairs, and one other spec without a run. An evidence-tier build using that temporary index assigned this ID `calibration`, with no exclusion or integrity finding and school-score eligibility false. Its local branch census moved **574 → 575 public-visible**; the total moved 2,142 → 2,144 because an unrelated, still-unrun teen-employment registration was already present in the branch base. The generated site indexes must be refreshed after integration.

## Stored results not promoted

The ten remaining small-queue leads below were compared with their registered rule and saved run. Their existing case-specific audits provide the full evidence; no old-ID metadata or verdict was edited.

| Archived ID | Why the saved result cannot pass its frozen claim |
| --- | --- |
| `oecd_epl_growth_shock_unemployment_persistence_panel` | Raw contrast is undefined; the saved negative-growth/EPL test cannot make its two-part decision. |
| `oecd_pdb_hours_reduction_output_tradeoff_panel` | Positive hours-growth coefficient makes the runner's support gate point against the English no-output-loss claim. |
| `developmentalist_growth_premium_low_income_only` | Two incompatible run packets and no matched pinned source for the later coefficient; income-stage interaction unmeasured. |
| `minimum_wage_youth_unemployment_tradeoff` | ILO youth and total outcomes were averaged over sex/age dimensions; youth-versus-total contrast unmeasured. |
| `resource_developmentalism_rent_seeking_trap` | Generic resource scalar/export proxy does not identify the registered subtype, diversification and TFP contrast. |
| `unemployment_benefit_generosity_employment_drag` | ILO employment count was treated as an employment-to-population rate; second outcome unmeasured. |
| `workfare_conditionality_employment_effect` | Modelled total 15+ WDI rate substitutes for the registered age 15–64 and long-term-unemployment tests. |
| `argentina_milei_disinflation_monetary_reconfiguration_2023_2028` | End-2026 durability window incomplete and reversal marker undefined. |
| `el_salvador_bukele_security_growth_equilibrium_2019_2026` | 2023–24 homicide cells missing; a 2022 value cannot establish the registered durability window. |
| `tariff_protection_duration_growth_drag` | Saved treatment is current tariff level, not registered cumulative duration; real-consumption endpoint and controls also lack frozen coverage. |

See `five_case_integrity_recovery_review_2026-10-09.md`, `ilostat_dimension_integrity_2026-10-09.md`, `verified_estimator_nonplaceholder_screen_2026-10-10.md`, and `tariff_protection_duration_frozen_repair_review_2026-10-09.md`. A new registration and independent source-backed result are required for any future rescue. No old archived ID gained public credit in this wave.
