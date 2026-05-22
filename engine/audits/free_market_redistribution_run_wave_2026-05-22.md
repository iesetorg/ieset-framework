# Free-Market / Redistribution Run Wave - 2026-05-22

## Summary

Ran the 15 clean first-pass candidates from
`engine/audits/free_market_redistribution_spec_wave_2026-05-22.md` with the
generic `scripts/run_panel_fe.py` runner.

| Verdict | Count |
| --- | ---: |
| SUPPORTED | 2 |
| PARTIAL | 8 |
| REFUTED | 3 |
| INCONCLUSIVE_DATA_PENDING | 2 |
| Total | 15 |

## Results

| hypothesis | verdict | coefficient | p-value | observations | note |
| --- | --- | ---: | ---: | ---: | --- |
| `market_dynamism_property_rights_investment_growth` | PARTIAL | -0.2159 | 0.805 | 967 | Wrong-signed, not significant. |
| `market_dynamism_private_credit_productivity_growth` | PARTIAL | +0.000433 | 0.175 | 850 | Right-signed, not significant. |
| `redistribution_tax_private_investment_drag_panel` | REFUTED | +0.6762 | 0.0000146 | 284 | Higher tax-revenue share predicts higher private investment in this first-pass panel. |
| `redistribution_public_consumption_tfp_drag_pwt_panel` | SUPPORTED | -0.008881 | 0.0422 | 1,071 | Higher public-consumption share predicts lower TFP. |
| `trade_openness_patent_diffusion_panel` | PARTIAL | +0.000665 | 0.797 | 917 | Right-signed, not significant. |
| `state_allocation_private_credit_innovation_panel` | REFUTED | +5.722 | 0.000176 | 897 | Government-consumption proxy predicts higher private-credit depth in this first-pass panel. |
| `price_signal_freedom_inflation_volatility_panel` | INCONCLUSIVE_DATA_PENDING | n/a | n/a | n/a | Treatment has no within-country variation under country fixed effects. |
| `market_dynamism_tariff_reduction_consumption_pc` | REFUTED | +0.001843 | 0.0722 | 1,021 | Higher tariff proxy is positively associated with consumption per capita in the first-pass panel. |
| `market_dynamism_export_diversification_growth` | PARTIAL | -0.000000 | 0.839 | 1,026 | Effect magnitude effectively zero. |
| `market_dynamism_government_consumption_investment_drag` | SUPPORTED | -0.3767 | 0.0262 | 1,079 | Higher government-consumption share predicts lower investment share. |
| `market_dynamism_investment_freedom_renewables_diffusion` | PARTIAL | +0.000931 | 0.408 | 850 | Right-signed, not significant. |
| `redistribution_progressive_tax_growth_threshold_oecd` | PARTIAL | -0.1130 | 0.151 | 877 | Right-signed, not significant. |
| `redistribution_market_income_growth_poverty_exit_panel` | PARTIAL | -0.000000 | 0.601 | 373 | Effect magnitude effectively zero. |
| `energy_market_competition_renewable_capacity_panel` | PARTIAL | +0.01273 | 0.770 | 902 | Right-signed, not significant. |
| `price_control_intensity_electricity_access_growth_panel` | INCONCLUSIVE_DATA_PENDING | n/a | n/a | n/a | Zero observations after listwise deletion. |

## Interpretation

This is a useful first-pass wave, but not scoreboard-ready by itself.

- The strongest positive market-process signal in this batch is the government
  consumption / investment drag result.
- The strongest redistribution/state-allocation challenge result is public
  consumption and TFP drag.
- The clearest refutations are important: broad tax-revenue share, state
  allocation proxied by government consumption, and tariff averages did not
  behave in the pro-market direction under the generic panel setup.
- Two price-control/price-signal specs need redesign because the current
  treatment proxies fail under fixed effects or delete the sample.
- Several specs have multi-outcome falsification language, while the generic
  runner grades the first loaded outcome. These need bespoke robustness checks
  before scoreboard mapping.

## Next Repairs

1. Split multi-outcome claims into separate single-outcome specs or add bespoke
   replication scripts that evaluate all preregistered outcomes.
2. Replace `heritage_ief:ief_panel` price-signal treatments with a within-country
   varying component or event-coded legal price-control index.
3. Recheck the refuted tax/private-investment and state-allocation/private-credit
   cases for treatment timing, lag structure, and whether the proxy is measuring
   public goods/state capacity rather than redistribution or command allocation.
4. Treat this as a triage wave: good candidates for refinement, not direct
   scoreboard conversion.
