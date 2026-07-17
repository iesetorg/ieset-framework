# Graduation Batch B Absorbed-Treatment Repair - 2026-05-16

Scope: the 10 Batch B candidates from `engine/audits/broad_hypothesis_graduation_plan_2026-05-16.md` whose latest diagnostics report no within-country treatment variation under country fixed effects.

Inputs read:

- `internal research notes`
- `engine/audits/broad_hypothesis_graduation_plan_2026-05-16.md`
- Batch B hypothesis YAMLs under `hypotheses/**`
- Current `engine/runs/<hypothesis_id>/diagnostics.json` and `result_card.md`

No hypothesis YAML, script, or run artifact was edited.

## Summary

| Bucket | Count | Candidate IDs |
| --- | ---: | --- |
| Ready low-risk YAML/schema patch | 3 | `universal_healthcare_cost_outcome_oecd`, `asia_pakistan_imf_programme_cycle_1988_2024`, `export_openness_agricultural_diversification` |
| Low-risk source mapping, but not graduation-safe until missing control is handled | 1 | `demo_life_expectancy_lfp_panel` |
| Correct fix changes the estimand or primary design | 4 | `asia_bangladesh_apparel_growth_1985_2024`, `china_soe_vs_cee_privatised_growth`, `australia_hawke_keating_reform_long_run`, `gfc_balance_sheet_recession_post_2008_household_dual_mandate` |
| Needs external/older data before design can be repaired | 2 | `oecd_product_market_deregulation_tfp_panel`, `demo_canada_points_system_immigration` |

Estimated immediate graduation yield from the 3 fully ready patches: **3 real verdicts**. In dry-run-in-memory checks, all three become estimable with the generic runner. Expected labels are likely `SUPPORTED` for the healthcare cross-country cost test, a real verdict for the Pakistan peer-difference test, and likely `PARTIAL` for the agricultural-diversification proxy. The life-expectancy source patch likely produces a real verdict too, but it should be treated as research-only until the statutory-pension-age control is present.

## Ready Low-Risk Patches

These are wrong fixed-effects or schema repairs that restore the written falsification test rather than changing it.

### `universal_healthcare_cost_outcome_oecd`

Current blocker: `treatment 'universal_healthcare_indicator' has no within-country variation under country fixed effects`.

Correct fix: **reduced fixed effects / cross-sectional OECD-year design**. The YAML's falsification test is already cross-country: USA residual spending vs OECD universal-system peers over 2010-2023. Country FE are simply wrong because they absorb the universal-system indicator.

Proposed edit in `hypotheses/healthcare/universal_healthcare_cost_outcome_oecd.yaml`:

```yaml
sample:
  period: [2010, 2023]

estimator:
  template: panel_fe
  clustering: country
  fixed_effects:
    - year
  notes: >
    Cross-country OECD-year regression for 2010-2023, matching the
    falsification test's USA-vs-OECD residual framing. Country fixed effects
    are intentionally omitted because the universal-healthcare indicator is
    a country/system design contrast and would be absorbed.
```

Rerun command after patch:

```bash
python3 scripts/run_panel_fe.py universal_healthcare_cost_outcome_oecd --force
```

### `asia_pakistan_imf_programme_cycle_1988_2024`

Current blocker: `treatment 'pakistan_indicator' has no within-country variation under country fixed effects`.

Correct fix: **reduced fixed effects**. The falsification threshold is the Pakistan-minus-SAARC-peer mean growth differential over 1990-2019. Year FE are useful to absorb shared shocks; country FE are not because the treatment is explicitly the Pakistan indicator.

Proposed edit in `hypotheses/growth/asia_pakistan_imf_programme_cycle_1988_2024.yaml`:

```yaml
sample:
  period: [1990, 2019]

estimator:
  template: panel_fe
  fixed_effects:
    - year
  clustering: country
  notes: >-
    Reduced-FE peer-difference design. Estimate the Pakistan indicator
    against SAARC peers with year fixed effects only, matching the
    preregistered PAK-minus-peer mean growth differential over 1990-2019.
    Country fixed effects are omitted because they absorb the Pakistan
    contrast by construction.
```

Rerun command after patch:

```bash
python3 scripts/run_panel_fe.py asia_pakistan_imf_programme_cycle_1988_2024 --force
```

### `export_openness_agricultural_diversification`

Current blocker: `treatment 'policy_or_institution_proxy' has no within-country variation under country fixed effects`.

Diagnosis: this is two problems stacked together. First, the current constructed source uses `from YYYY onward`, which the generic constructed parser currently materializes as a one-year pulse for this pattern. Second, the WGI `rule_of_law` control begins after the 1975/1984/1988 treatment onsets, so listwise deletion leaves only post-treatment observations. That makes the treatment country-constant in the estimation sample.

Correct fix: **event-style staggered panel/TWFE with a valid post indicator**, while moving WGI to robustness-only. This keeps the same proxy treatment and outcome.

Proposed edit in `hypotheses/trade/export_openness_agricultural_diversification.yaml`:

```yaml
variables:
  treatment:
  - name: policy_or_institution_proxy
    source: "constructed: CHL years >= 1975; NZL years >= 1984; VNM years >= 1988"
    transformation: indicator_or_level
  controls:
  - name: log_gdp_pc
    source: world_bank_wdi:NY.GDP.PCAP.KD
    transformation: log

estimator:
  template: panel_fe
  fixed_effects:
    - country
    - year
  clustering: country
  notes: >
    Proxy-first staggered reform panel. `rule_of_law` is excluded from the
    primary model because WGI starts after all three treatment onsets and
    mechanically deletes the identifying pre-reform years; it should be
    reported only as a post-1996 robustness/descriptive check.
```

Rerun command after patch:

```bash
python3 scripts/run_panel_fe.py export_openness_agricultural_diversification --force
```

## Low-Risk Source Patch, But Not Graduation-Safe Yet

### `demo_life_expectancy_lfp_panel`

Current blocker: `treatment 'life_expectancy_at_60' has no within-country variation under country fixed effects`.

Diagnosis: the source token `who_gho:LIFE_0000000035` is not on disk. The treatment was accidentally constructed from the note text; the phrase "at 60" caused `AT` to be interpreted as Austria, producing an Austria dummy with no within-country variation. A local WHO GHO life-expectancy-at-60 vintage does exist as `who_gho:WHOSIS_000015`.

Correct fix: **different treatment variable/source mapping**, not an FE change. Keep country and year FE after the source is corrected.

Proposed edit in `hypotheses/labour/demo_life_expectancy_lfp_panel.yaml`:

```yaml
variables:
  treatment:
    - name: life_expectancy_at_60
      source: who_gho:WHOSIS_000015
      transformation: level
      notes: >
        WHO GHO WHOSIS_000015 life expectancy at age 60. Current generic
        loader averages sex-specific rows to country-year.
```

Rerun command after patch, if a research-grade run is acceptable:

```bash
python3 scripts/run_panel_fe.py demo_life_expectancy_lfp_panel --force
```

Graduation caveat: the current diagnostics still miss the preregistered `statutory_pension_age` control and `lfp_65_plus` secondary outcome. The source patch is safe, but the result should not be treated as fully claim-complete until the pension-age source is mapped or the falsification rule is explicitly narrowed.

## Design Or Estimand Decision Required

These should not be quiet YAML patches because the correct fix changes the identifying design, treatment, or primary test.

### `oecd_product_market_deregulation_tfp_panel`

Current blocker: `treatment 'oecd_pmr_overall_index' has no within-country variation under country fixed effects`. The loaded PMR data are effectively 2018/2023 only, while the sample ends in 2019, leaving only one PMR year in-sample. The YAML claims 1998-2019 deregulation predicting subsequent TFP growth.

Correct fix: **needs older PMR waves or a different treatment variable**. A reduced-FE 2018 cross-section would not test "reductions" or "following 5-year growth"; extending to 2023 changes the period and runs through COVID/reopening.

Not ready. Proposed design options:

- Fetch/restore older OECD PMR waves, then use `transformation: diff` or a dedicated `pmr_reduction_5yr` constructed variable with country and year FE.
- If only 2018/2023 PMR is available, rewrite as a 2018-2023 cross-sectional/descriptive screen and mark it as a new estimand.

No rerun command recommended until data/design is chosen.

### `asia_bangladesh_apparel_growth_1985_2024`

Current blocker: `treatment 'post_1985_epz_indicator' has no within-country variation under country fixed effects`. This is structural: the sample starts in the treatment year, so Bangladesh is always treated.

Correct fix: **cross-sectional/descriptive or bespoke multi-metric checklist**. The falsification rule is not a TWFE coefficient; it asks for two deterministic thresholds: Bangladesh manufacturing share change 1985-2019 and Bangladesh-minus-Pakistan GDP-per-capita growth differential over 2000-2019.

Not ready for a generic runner without changing the estimand. Proposed YAML direction:

```yaml
estimator:
  template: descriptive
  notes: >
    Bespoke two-part descriptive threshold: BGD manufacturing value-added
    share change 1985-2019 and BGD-minus-PAK real GDP-pc growth differential
    over 2000-2019. Do not estimate a country-FE treatment coefficient.
```

No generic rerun command recommended. `scripts/run_descriptive.py` does not currently evaluate both preregistered thresholds.

### `china_soe_vs_cee_privatised_growth`

Current blocker: `treatment 'china_soe_strategic_sector_indicator' has no within-country variation under country fixed effects`.

Correct fix: **different treatment variable**. The China indicator is a country dummy and cannot identify an ownership-form effect under country FE. The spec already has a plausible time-varying alternative, `privatisation_intensity`, but making it primary changes the estimand from "China strategic SOEs vs CEE peers" to "privatisation/enterprise-restructuring intensity and industrial/manufacturing outcomes".

Not ready. Proposed YAML direction after owner sign-off:

```yaml
variables:
  treatment:
    - name: privatisation_intensity
      source: ebrd:transition_indicators
      transformation: level
      notes: "Time-varying EBRD large-scale privatisation / enterprise-restructuring proxy; primary treatment for CEE transition intensity."
    - name: china_soe_strategic_sector_indicator
      source: "constructed: indicator = 1 for CHN; 0 for CEE/post-Soviet peers"
      transformation: indicator
      notes: "Descriptive China-vs-peer contrast only; not identified with country FE."
```

Rerun would remain `python3 scripts/run_panel_fe.py china_soe_vs_cee_privatised_growth --force`, but only after rewriting the falsification rule and expected sign around the new primary treatment.

### `demo_canada_points_system_immigration`

Current blocker: `treatment 'points_system_indicator' has no within-country variation under country fixed effects`; additionally, `foreign_born_tertiary_share` from OECD DIOC is missing.

Correct fix: **reduced fixed effects / cross-sectional design once the outcome exists**, plus possible treatment recoding. The claim is mostly a Canada-vs-OECD skill-selection premium, not a within-country treatment effect. The disclosure also notes that Australia and New Zealand are points-system comparators, so leaving them coded as zero may be a treatment-definition error.

Not ready. Proposed direction:

- Map/fetch OECD DIOC `foreign_born_tertiary_share`.
- Decide whether treatment is `CAN` only or points-system countries `CAN/AUS/NZL`.
- Use year FE only for the cross-country skill-premium regression, or use a descriptive Canada-vs-OECD median test.

No rerun command recommended until the DIOC outcome and treatment coding are fixed.

### `australia_hawke_keating_reform_long_run`

Current blocker: `treatment 'australia_post_1983' has no within-country variation under country fixed effects`.

Diagnosis: the source text `1 for AUS from 1983 onward` is susceptible to the same one-year constructed-parser issue, but the deeper problem is design: the sample starts in 1983, so there is no pre-reform Australia period. WGI controls also begin after 1983 and would delete any pre-reform years if added.

Correct fix: **synth-DiD/synthetic control** with pre-1983 data. This is conceptually consistent with the YAML's secondary design and falsification threshold (`synthetic_gap > 0`), but it changes the primary estimator away from the registered panel-FE beta.

Not low-risk without owner sign-off. Proposed edit if the design conversion is accepted:

```yaml
sample:
  period: [1970, 2019]
  exclusion_rules:
    - "exclude COVID 2020-2021"

variables:
  treatment:
    - name: australia_post_1983
      source: "constructed: AUS years >= 1983"
      transformation: binary

estimator:
  template: synth_did
  event_year: 1983
  clustering: country
  notes: >
    Primary synthetic-control/synth-DiD for AUS using commodity-exporting and
    small-open-economy donors. Generic runner uses the first country as treated
    and the remaining sample countries as donors. WGI controls are descriptive
    robustness only because they begin after treatment onset.
```

Rerun if accepted:

```bash
python3 scripts/run_synth_did.py australia_hawke_keating_reform_long_run --force
```

### `gfc_balance_sheet_recession_post_2008_household_dual_mandate`

Current blocker: `treatment 'household_saving_rate' has no within-country variation under country fixed effects`.

Diagnosis: the OECD sectoral-account source is not on disk. As with the life-expectancy case, the generic constructed fallback misread text in the variable note and produced an Austria dummy. The spec also requires three separate tests: household saving/deleveraging, NFC net lending turning positive, and fiscal absorption predicting shallower output loss.

Correct fix: **data/source mapping plus descriptive/reduced-FE multi-metric design**. A single panel-FE coefficient on `household_saving_rate` is not the registered estimand.

Not ready. Required before rerun:

- Fetch/map OECD household saving rate.
- Fetch/map OECD nonfinancial corporate net lending to GDP.
- Map short-rate/ZLB control or explicitly downgrade it.
- Use a bespoke checklist/descriptive-plus-cross-sectional regression wrapper for the three-pronged rule.

No generic rerun command recommended.

## Blockers

Top blockers across Batch B:

1. Country-constant policy/system indicators were paired with country FE (`universal_healthcare`, `pakistan_indicator`, `points_system_indicator`, China/Bangladesh/Australia country dummies).
2. Some constructed source strings accidentally create one-year pulses or dummy variables from prose (`from YYYY onward`; `at 60`; `rate` containing `AT`).
3. Key controls start after the treatment event and delete all pre-treatment identifying years (`rule_of_law`, WGI government effectiveness).
4. Several hypotheses are really descriptive or multi-metric threshold tests, while the generic panel-FE runner grades only one treatment coefficient.
5. Missing data still blocks clean graduation for OECD PMR history, OECD DIOC foreign-born education, OECD pension age, and OECD sectoral-account net-lending series.
