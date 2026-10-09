# ILO dimension and endpoint integrity audit — 2026-10-09

## Finding

The historical generic panel runner loads some ILO sex-by-age files, then normalizes them to country, year, and value. When multiple rows share a country-year, `normalise_panel()` averages their values without retaining or filtering sex and age. The generic `panel_fe` path fits only the first listed outcome and first listed treatment. A result card naming a subgroup or a second outcome does not prove either was estimated. This audit inspected source keys, dimensions, specs, runner paths, and saved diagnostics; it did not reinterpret historical coefficients as the named subgroups.

The dimensioned EAP file has 27 sex-by-age rows per country-year; the UNE and EMP-number files have nine each. Eleven saved runs actually loaded a dimensioned ILO outcome through the generic runner. Three were public calibration and eight already archived; none was featured. One additional archived decomposition case loaded ILO unemployment as a channel. These are scope findings, not a claim that all twelve primary coefficients have the same defect.

## Immediate public-evidence correction

| Hypothesis | Saved-result mismatch | Disposition |
| --- | --- | --- |
| `minimum_wage_youth_unemployment_tradeoff` | Youth and total outcomes both resolve to the same unfiltered ILO unemployment sex-by-age file. The runner averaged the dimensions and fitted only the first outcome; the registered youth-versus-total comparison was not measured. | External integrity quarantine; original run retained. |
| `unemployment_benefit_generosity_employment_drag` | The named employment-to-population ratio resolves to an ILO employment **count** file. The runner averaged sex/age counts without a population denominator; the registered rate and secondary unemployment test were not measured. | External integrity quarantine; original run retained. |
| `workfare_conditionality_employment_effect` | The primary bridge uses WDI's modelled total age-15-plus employment-to-population rate, while the card presents a broader age-15-to-64, five-year and long-term-unemployment rule. The secondary ILO file is generic unfiltered unemployment and was not fitted. | External integrity quarantine pending a scoped primary-only result or a new prospective direct test; original run retained. |

The exact hold and reasons are in `engine/public_evidence_quarantines.json`. The public evidence-tier audit now marks these three as archive, makes school-score eligibility false, and sets a zero score cap. Their 18 structural school-claim links remain historical mapping metadata; a mapping check is not an empirical test. The saved `PARTIAL` diagnostics and run artifacts were not rewritten.

## Archive review queue

Eight other dimensioned-ILO-outcome runs were already archived and need claim-specific endpoint review before any prospective repair: `activation_sanctions_reemployment_duration_panel`, `demo_life_expectancy_lfp_panel`, `demo_mexico_fertility_decline_wages`, `demo_remittance_corridor_dependency`, `india_services_led_growth_employment_effect`, `oecd_taxben_benefit_cliff_lfp_penalty`, `temporary_contract_restrictions_youth_hiring_panel`, and `unconditional_transfer_work_hours_response_panel`. The archived `demo_brazil_demographic_transition_inequality` also loaded ILO unemployment as a decomposition channel. Do not promote these by relabeling the old fits.

The new `remittance_share_male_prime_age_lfp_country_holdout_v2` is an explicitly registered endpoint repair. It selects the physical ILO male age-25-to-54 slice, excludes all 13 countries in the old mixed-dimension fit, caps the modelled series at 2023, and grants only descriptive calibration credit after read-only replay. Its old result remains archived and is not treated as a valid male-subgroup comparator.

## Next repair gate

For each affected claim, freeze the exact ILO indicator, sex, age, status, unit, source vintage, country roster, time window, and all required outcomes before numeric analysis. A runner must reject duplicate selected keys and mismatched source/normalized values, preserve the historical result as an audit trail, and report non-results as inconclusive. Public and school credit requires a new registered result and the normal evidence audit; source-label or verdict edits alone cannot repair the endpoint.
