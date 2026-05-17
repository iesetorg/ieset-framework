# High-quality graduation batch 5 - 2026-05-16

This batch targeted specs where the existing generic runner was using the wrong estimand for an otherwise concrete registered gate. I avoided upgrading the stricter BLS productivity-compensation spec because its local BLS vintages only contain 2023-2025 growth-rate observations, not the required 1973 and 2019 endpoints. The FRED sibling remains the appropriate supported artifact for that question.

## Runner upgrades

- `scripts/run_descriptive.py`
  - Added a raw-daily FRED `RRPONTSYD` peak/decline gate for `financial_fed_reverse_repo_facility_usage_2021_2024`.
  - This bypasses annual mean aggregation, which is inappropriate for a peak/trough claim.
- `scripts/run_local_projections.py`
  - Added a TCJA pre-COVID threshold check for `tcja_2017_growth_effect`.
  - Uses quarterly FRED `GDPC1` and `PNFI`, fits a log-linear 2010Q1-2017Q3 pretrend, and evaluates 2018Q1-2019Q4 gaps.
- `scripts/run_event_study.py`
  - Added an annual Census SPM fallback gate for `welfare_transfer_us_arpa_expanded_ctc_2021`.
  - Uses `us_census:spm_child_poverty_rate` only as a conservative fallback for the preferred CPSP monthly series.

## Graduated artifacts

| Hypothesis | Verdict | Main result | Caveat |
| --- | --- | --- | --- |
| `financial_fed_reverse_repo_facility_usage_2021_2024` | SUPPORTED | ON RRP peaked at USD 2,553.7bn on 2022-12-30 and fell USD 2,314.3bn to the 2024Q3 low. Both the USD 2,000bn peak and USD 1,500bn decline gates clear. | None material; this is a direct descriptive FRED gate. |
| `tcja_2017_growth_effect` | WEAKENED | Real GDP was only +0.975pp above the 2010Q1-2017Q3 pretrend over 2018-2019, clearing the <1pp output-response gate. Private nonresidential fixed investment averaged -3.73% below its pretrend. | The registered EMTR-elasticity gate is still not machine-loaded, so this is not full support. |
| `welfare_transfer_us_arpa_expanded_ctc_2021` | WEAKENED | Census SPM child poverty fell 4.5pp from 2020 to 2021 and rebounded 7.2pp from 2021 to 2022, clearing the poverty drop/rebound gates. | Preferred CPSP monthly poverty and parental-LFP six-month ATT gates are not loaded. |

## Candidate explicitly not upgraded

- `productivity_compensation_decoupling_post_1973`
  - Remains `INCONCLUSIVE_DATA_PENDING`.
  - The spec requires BLS `PRS85006092` and `PRS85006112` endpoints at 1973 and 2019. The current BLS vintages each have only 12 quarterly growth-rate rows for 2023-2025, so using them would violate the method-validity gate.
  - The related FRED-only artifact `fred_productivity_compensation_gap_us_1973_2025` is already supported, but it is not a substitute for the stricter composition-adjusted BLS endpoint test.

## Verification

- `python3 -m py_compile scripts/run_descriptive.py scripts/run_local_projections.py scripts/run_event_study.py`
- Targeted reruns:
  - `python3 scripts/run_descriptive.py financial_fed_reverse_repo_facility_usage_2021_2024 --force`
  - `python3 scripts/run_local_projections.py tcja_2017_growth_effect --force`
  - `python3 scripts/run_event_study.py welfare_transfer_us_arpa_expanded_ctc_2021 --force`
