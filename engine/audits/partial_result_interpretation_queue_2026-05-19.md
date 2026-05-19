# Partial-Result Interpretation Queue — 2026-05-19

Purpose: keep `PARTIAL` verdicts useful without letting them become lazy scoreboard fuel.
The rule for this pass is:

- convert only when the partial result has a clear directional leg, complete local data, and a narrow school claim;
- split when one mechanism is supported and another failed or remains data-gated;
- hold when the result is direction-inconclusive, claim-direction ambiguous, or still missing primary data.

## Converted This Pass

| Hypothesis | Verdict interpretation | Scoreboard action |
|---|---|---|
| `capital_gains_tax_cut_investment_response_panel` | Hash-verified panel. Capital-gains tax rate is negative and significant for investment (`coef=-0.202`, `p=0.0015`), but the business-entry outcome is not significant. This is partial support for the investment-incentive channel, not full support for the entrepreneurship claim. | Added reciprocal partial-support links to `classical_liberal` claim 197 and `chicago_monetarism` claim 150. |

## Split Before More Scoreboard Conversion

| Hypothesis | What the partial really says | Next testable split |
|---|---|---|
| `monetary_finance_deficit_currency_collapse_chain` | Currency depreciation is confirmed in 4/6 cases, but the inflation-acceleration leg misses the full threshold. | Split into a currency-depreciation first-stage hypothesis and an inflation pass-through second-stage hypothesis. |
| `hyperinflation_requires_fiscal_dominance` | All 29 parsed Hanke post-1900 episodes are fiscal-dominance cases, but 23 rows remain parser-pending. | Finish Hanke table parsing, then rerun as a high-value monetary/fiscal-dominance test. |
| `green_transition_cost_trajectory_electricity_prices` | Electricity-price gap is visible; manufacturing-output underperformance is not confirmed in WDI. | Split price-channel evidence from industrial-output effect; add ENTSO-E/Eurostat industrial production before remapping. |
| `singapore_temasek_public_ownership_efficiency` | Singapore clears GDP-per-capita growth and institutional-quality gates but misses the PWT TFP metric. | Split public-holding governance/outcome case from a narrower TFP-efficiency claim. |
| `cuba_health_outcomes_vs_non_latam_market_peers` | Cuba clears two of three harder non-LatAm market-peer gates but misses the IMR rank threshold. | Keep as harder-benchmark partial; do not treat as the same as the LatAm-peer support case. |

## Hold For Data Repair Or Re-Run

| Hypothesis | Hold reason | Needed repair |
|---|---|---|
| `federal_minimum_wage_employment_meta` | Local state FE elasticity is near zero, but confidence interval is too wide to validate equivalence. | Add BLS state teen employment-population, QCEW, and bite-ratio panel. |
| `oecd_union_density_disposable_gini_panel` | Point estimate has the predicted sign but is too small/imprecise for support. | Expand OECD redistribution/labour-market panel and re-run with disposable-income controls. |
| `uk_cameron_osborne_austerity_output_effect` | Debt-target miss is clear, but output underperformance threshold is not met. | Re-run with richer donor pool and fiscal-impulse controls before mapping beyond existing partial links. |
| `oecd_product_market_deregulation_tfp_panel` | Short-window PMR decline proxy does not clear both productivity gates. | Use longer PMR vintage or sector PMR/Productivity by industry; short window is too noisy. |
| `capital_mobility_worker_bargaining_power` | Direction is plausible but imprecise. | Add capital-flow restrictions, union density, and wage-share interaction panel. |

## Do Not Convert As-Is

These partials use phrases like `direction inconclusive`, `effect magnitude effectively zero`,
or `claim direction ambiguous`. They should stay out of new scoreboard mapping until the
claim is rewritten or the replication script emits a direction-safe verdict:

- `rent_control_housing_supply_quality_decay_chain`
- `price_controls_shortage_black_market_progression`
- `precautionary_regulation_innovation_productivity_gap_eu_us`
- `resource_rent_capture_outperforms_laissez_faire`
- `nuclear_phaseout_energy_cost_industry_exit`
- `regulatory_quality_fdi_spillover`
- `exchange_rate_volatility_investment_horizon`
- `federalism_market_experimentation`

## Throughput Implication

The biggest near-term partial unlock is not indiscriminate mapping. It is finishing
the split tests above, especially Hanke fiscal-dominance parsing, EU energy/output
data, BLS minimum-wage panels, and OECD union/redistribution panels. Those are the
partials most likely to become clean `SUPPORTED` or `REFUTED` verdicts after one
data pass.
