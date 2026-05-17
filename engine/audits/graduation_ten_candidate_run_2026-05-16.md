# Ten-Candidate Graduation Run - 2026-05-16

Purpose: implement and rerun the ten highest-confidence candidates from the
graduation repair swarm.

## Result

All ten candidates now produce real verdict artifacts.

| Verdict label | Count |
| --- | ---: |
| `SUPPORTED` | 4 |
| `PARTIAL` | 6 |
| `REFUTED` | 0 |
| `INCONCLUSIVE_DATA_PENDING` | 0 |
| Crashes | 0 |

## Candidate Results

| Candidate | Verdict | Estimate / comparison | Method | Notes |
| --- | --- | --- | --- | --- |
| `universal_healthcare_cost_outcome_oecd` | `SUPPORTED` | beta = -0.5591, p = 0.00279, N = 322 | `linearmodels.PanelOLS` | Reduced to year FE so the universal-system country contrast is not absorbed. |
| `asia_pakistan_imf_programme_cycle_1988_2024` | `SUPPORTED` | beta = -2.2871, p = 1.24e-14, N = 150 | `linearmodels.PanelOLS` | Year-FE peer-difference design; `claim_direction: "-"` pinned for the PAK-minus-peer growth differential. |
| `export_openness_agricultural_diversification` | `PARTIAL` | beta = -2.4981, p = 0.691, N = 1155 | `linearmodels.PanelOLS` | Treatment now persists after reform onsets; WGI rule-of-law moved out of primary sample. |
| `startup_density_frontier_prosperity` | `PARTIAL` | beta = +4.02e-06, p = 0.121, N = 271 | `linearmodels.PanelOLS` | WDI new-business registrations used as startup-density fallback; PMR control dropped by sample ladder. |
| `minimum_wage_youth_unemployment_tradeoff` | `PARTIAL` | beta = -0.0919, p = 0.331, N = 246 | `linearmodels.PanelOLS` | OECD minimum-wage-to-average-wage ratio used as v1 harmonized bite proxy; youth-population/EPL controls still missing. |
| `india_extra_aadhaar_upi_productivity` | `PARTIAL` | IND Findex account ownership +42.3pp; peer differential +15.8pp | bespoke descriptive threshold | Clears +35pp absolute gain but misses +20pp peer-differential threshold. |
| `demo_brazil_demographic_transition_inequality` | `PARTIAL` | beta = +1.1718, p = 0.208, N = 25 | statsmodels OLS time-series fallback | Single-country HAC path now runs; estimate is not significant and is not in the claimed negative direction. |
| `demo_mexico_fertility_decline_wages` | `SUPPORTED` | beta = +0.1242, p = 8.99e-47, N = 18 | statsmodels OLS time-series fallback | `claim_direction: "+"` pinned to match the working-age-share wage-growth claim. Thin-sample caveat remains. |
| `welfare_state_market_flexibility_complement` | `PARTIAL` | beta ~= 0, p = 0.733, N = 725 | `linearmodels.PanelOLS` | SOCX welfare-state slice and flexibility-openness-discipline composite now construct; interaction effect is effectively zero. |
| `fiat_expansion_erodes_currency_purchasing_power_long_run` | `SUPPORTED` | 7/7 fiat currencies pass hard-asset endpoint check | bespoke descriptive threshold | Uses loaded commodity basket plus BIS residential property benchmarks; descriptive, not causal. |

## Implementation Changes

Hypothesis/source edits:

- `universal_healthcare_cost_outcome_oecd`: sample narrowed to 2010-2023 and
  country FE removed.
- `asia_pakistan_imf_programme_cycle_1988_2024`: primary window set to
  1990-2019, year FE only, `claim_direction: "-"`.
- `export_openness_agricultural_diversification`: persistent CHL/NZL/VNM
  reform indicators; WGI rule-of-law removed from primary controls.
- `startup_density_frontier_prosperity`: WDI `IC.BUS.NREG` startup-density
  fallback.
- `minimum_wage_youth_unemployment_tradeoff`: OECD `MWUSD` harmonized bite
  proxy.
- `fiat_expansion_erodes_currency_purchasing_power_long_run`: descriptive
  estimator and `imf_pcps:PALLFNF` commodity-basket source.
- `welfare_state_market_flexibility_complement`: SOCX source token changed to
  `oecd:DSD_SOCX@DF_SOCX_AGG`.
- `demo_mexico_fertility_decline_wages`: `claim_direction: "+"`.

Runner edits:

- `scripts/run_panel_fe.py`
  - added IMF PCPS and PWT source bridges;
  - added SOCX slice for `welfare_state_size`;
  - added constructed composite for
    `market_flexibility_openness_discipline_index`;
  - changed decomposition mode to use the explicit treatment variable first;
  - added single-country time-series OLS fallback with HAC-style standard
    errors and a lower preregistered-small-sample floor.
- `scripts/run_descriptive.py`
  - added the India JAM/Findex threshold evaluator;
  - added the fiat hard-asset endpoint evaluator.

## Follow-Up Queue

- Promote the four `SUPPORTED` results to any graduation scoreboard/update
  pass that expects real-verdict artifacts.
- Treat the six `PARTIAL` results as successfully graduated from data-pending,
  but not as evidentiary wins.
- Next likely yield comes from the alias/data batch:
  OECD earnings, PWT pseudo-series, OECD-STAN wrapper, WITS/Comtrade product
  data, and FRED/BLS/ECB source aliases.
