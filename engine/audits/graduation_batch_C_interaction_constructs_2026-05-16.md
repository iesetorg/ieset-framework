# Graduation Batch C Interaction Constructs - 2026-05-16

Purpose: review the six Batch C hypotheses whose current diagnostics stop on
"interaction term requested but no loadable constructed interaction variable is
defined." Scope is audit only: no script, YAML, or run-artifact edits.

## Runner Support Read

`scripts/run_panel_fe.py` currently has two relevant mechanisms:

- `construct_variable_from_text(...)` can build simple `constructed:` indicators
  and weighted sums when the constructed string is parseable and component
  source tokens load.
- `construct_interaction_term(...)` is the safe primary path for Batch C. If a
  spec text asks for an interaction and the treatment block has at least two
  loaded treatment variables, it creates
  `__interaction_<component1>_x_<component2>`, makes that product the primary
  treatment, and keeps the component main effects as extra regressors.

Important guardrail: do not add a named treatment item containing
`interaction` unless that exact item is guaranteed to load. A missing explicit
interaction item can suppress the "do not grade main effects" guard and let the
runner fall through to a main-effect treatment. The safer minimal repair is:
make the two preregistered component treatment variables load, leave them as
the first two treatment items, and let `construct_interaction_term(...)` create
the product.

## Candidate Review

| hypothesis_id | interaction components | both components currently load? | minimal construction path | status |
| --- | --- | --- | --- | --- |
| `incumbent_subsidy_market_share_persistence` | Not a primary interaction. The detector is tripping on robustness-note text: "EU membership x sectoral-regulation timing". The primary treatment is incumbent subsidy/state aid. | No. No treatment loads. Diagnostics miss `incumbent_subsidy_share_gdp`, `state_aid_share_gdp`, `top_4_concentration_change_10yr`, and `initial_top4_concentration`. | Do not construct an interaction. Once treatment/concentration data exist, reword the robustness note or narrow detection so an IV phrase does not block a main-effect estimand. | blocked |
| `policy_uncertainty_private_investment` | `policy_uncertainty_index` x `state_led_reform_shift_indicator` | No. Diagnostics miss `policy_uncertainty_index`, `epu_index`, and `state_led_reform_shift_indicator`. | After data repair, load both as ordinary treatment variables and let the runner auto-create the product. The current weighted formula is not enough because `epu:national_index`, `election_frequency_volatility`, and `regulatory_turnover_rate` do not load, and the reform-shift indicator has no country-year episode map. | blocked |
| `welfare_state_market_flexibility_complement` | `welfare_state_size` x `market_flexibility_openness_discipline_index` | No under current YAML/script. Underlying raw inputs are local: OECD SOCX loads via `oecd:DSD_SOCX@DF_SOCX_AGG`/`oecd:SOCX_AGG`; OECD PMR, OECD EPL, WDI trade openness, and IMF debt all load. | Add a SOCX slice for welfare-state size and a constructed composite builder for the flexibility-openness-discipline index. Keep both variables as the first two treatment items; do not add an explicit interaction item. | ready_to_patch |
| `east_asia_export_discipline_vs_domestic_protection` | `export_orientation_index` x `domestic_protection_index` | No. Diagnostics miss all treatment variables. WDI export share and high-tech export share load, but the protection component lacks a long-panel tariff/NTB source; OECD PMR protection only covers a thin late-period subset. | After WITS/NTB/protection data exist, build export-orientation and domestic-protection composites, then let auto-interaction create the product. Do not use the late PMR-only slice as the full 1960-2020 estimand. | blocked |
| `universal_vs_meanstest_child_poverty` | `universal_child_benefit_dummy` x `family_benefit_spending_share_of_gdp` | No. Diagnostics miss the derived regime dummy and the SOCX family-benefit component. | Family-benefit SOCX is locally recoverable with a precise `TP51` public percent-GDP slice, but the universal-vs-means-tested country-year classification is not present. Also this spec is still `draft` with a stub rule, so do not force a verdict until the classification and threshold are promoted. | blocked |
| `industrial_policy_corruption_interaction` | `industrial_policy_intensity` x `low_rule_of_law_dummy` | No. Diagnostics miss both treatment variables. WGI `RL.EST` loads, so the low-rule-of-law dummy is constructible, but `industrial_policy_intensity` lacks a defensible local subsidy/state-aid source. | Add a median-split WGI builder only after a real industrial-policy-intensity source is available. Do not substitute broad public expenditure for subsidies/state aid; that would change the estimand. | blocked |

## Ready To Patch

### 1. `welfare_state_market_flexibility_complement`

Why safe: the preregistered interaction components are explicit, both component
data families exist locally, and the runner already has the correct product
construction behavior once both treatment variables load.

Exact changes:

1. In `scripts/run_panel_fe.py`, extend `_filter_oecd_socx_slice(...)`:

   - For `variable_name == "welfare_state_size"`, select:
     - `UNIT_MEASURE == "PT_B1GQ"`
     - `EXPEND_SOURCE == "ES10"`
     - `PROGRAMME_TYPE == "_T"`
     - prefer `SPENDING_TYPE == "_T"` when present
     - prefer `PRICE_BASE == "_Z"` when present
   - Return this slice before `normalise_panel(...)` aggregates to
     country-year values.

2. In `scripts/run_panel_fe.py`, add a direct constructed branch in
   `construct_variable_from_text(...)` for
   `market_flexibility_openness_discipline_index` when the source text contains
   PMR/EPL/trade/debt language:

   - load `oecd_pmr:PMR` as PMR, inverted
   - load `oecd:EPL_OV` as EPL, inverted
   - load `world_bank_wdi:NE.TRD.GNFS.ZS` as trade openness
   - load `imf:GGXWDG_NGDP` as debt-to-GDP, converted to an inverted penalty
     for debt above 90 percent
   - merge on `country_iso3, year`
   - z-score available components and average row-wise with a minimum of two
     non-null components
   - return `country_iso3, year, market_flexibility_openness_discipline_index`

3. In `hypotheses/fiscal/welfare_state_market_flexibility_complement.yaml`,
   change only the welfare-state source token:

   ```yaml
   - name: welfare_state_size
     source: "oecd:DSD_SOCX@DF_SOCX_AGG"
     transformation: level
   ```

4. Leave the two treatment variables in their current order and do not add a
   third explicit interaction variable. Existing `construct_interaction_term`
   should then create
   `__interaction_welfare_state_size_x_market_flexibility_openness_discipline_index`
   as the primary coefficient while including both main effects.

Optional non-primary cleanup: change `employment_rate` from
`oecd_lfs:employment_rate_15_64` to `oecd:DSD_LFS_BS@DF_EMP_RATE` if channel
coverage is desired, but this is not required for the primary graduation rerun.

Suggested rerun after patch:

```bash
python3 scripts/run_panel_fe.py welfare_state_market_flexibility_complement --force
```

Expected yield: 1 likely real verdict if the PMR-limited overlap remains above
the estimator sample floor after controls. Residual risk is a small sample after
listwise deletion, not interaction construction.

## Blocked Subset

### `incumbent_subsidy_market_share_persistence`

Blocker: false interaction detection plus missing primary data. The candidate
does not ask for an interaction as its primary estimand. The phrase
`membership x sectoral-regulation timing` appears only in an IV robustness note.
Even after removing the false interaction blocker, the run still lacks incumbent
subsidy/state-aid and concentration data.

Next safe repair: move to data/mapping lane. Add OECD STAN concentration and
state-aid/subsidy data first; then reword the IV note to avoid the `x` detector
or narrow `requests_interaction_without_constructed_term(...)` to primary
estimand text.

### `policy_uncertainty_private_investment`

Blocker: both interaction components are absent. `academic:baker_bloom_davis_epu`
and `epu:national_index` do not load, and `constructed: indicator = 1 for
large_state_intervention_episodes` has no country-year target map.

Next safe repair: fetch/map EPU or a vetted uncertainty panel, and add a
country-year reform-shift episode table. Then keep
`policy_uncertainty_index` and `state_led_reform_shift_indicator` as the first
two treatment variables and let the runner create the interaction.

### `east_asia_export_discipline_vs_domestic_protection`

Blocker: domestic protection is not available as a long East Asia panel. WDI
export variables load, but OECD PMR protection/tariff data cover only a late and
thin subset, not the preregistered 1960-2020 test.

Next safe repair: add WITS tariff and a non-tariff/protection proxy with enough
historical coverage, then build the two composites. A PMR-only late-period patch
would grade a different hypothesis.

### `universal_vs_meanstest_child_poverty`

Blocker: the universal/means-tested regime classification is missing, and the
spec is still draft/stubbed. SOCX family spending can be filtered locally, but
without the regime dummy the interaction cannot be constructed.

Next safe repair: create `derived:eu_child_benefit_regime` as a country-year
classification with provenance, add a SOCX `TP51` public percent-GDP filter, and
promote/sharpen the draft falsification rule before rerun.

### `industrial_policy_corruption_interaction`

Blocker: industrial-policy intensity is missing. The low-rule-of-law dummy can
be constructed from local WGI `RL.EST`, but the state-aid/subsidy component is
not present. V-Dem corruption also needs a source alias/slice if the corruption
outcome is to be used.

Next safe repair: add a defensible industrial-policy-intensity panel or source
bridge. Only then add a WGI median-split dummy builder and let the runner auto
multiply the two treatment components.

## Yield Estimate

- `ready_to_patch`: 1 of 6.
- Near-term graduation yield from this lane alone: 1 likely, 0-1 conservative.
- Remaining five require data/source mapping or design promotion before
  interaction construction would be safe.

Top blockers:

1. Missing state-aid/subsidy/industrial-policy-intensity panels.
2. Missing EPU and reform-shift episode data.
3. Missing child-benefit regime classification.
4. Missing long-panel East Asia protection data.
5. One false-positive interaction detector hit from robustness-note text.
