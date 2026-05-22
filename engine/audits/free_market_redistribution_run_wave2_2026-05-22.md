# Free-Market / Redistribution Run Wave 2 - 2026-05-22

## Summary

Ran the remaining 17 candidate specs from the 32-spec free-market /
redistribution wave. This completes first-pass run coverage for the whole wave:
all 32 new specs now have `engine/runs/<hypothesis_id>/` artifacts.

| Verdict | Count |
| --- | ---: |
| SUPPORTED | 2 |
| PARTIAL | 4 |
| REFUTED | 1 |
| INCONCLUSIVE_DATA_PENDING | 10 |
| Total | 17 |

## Results

| hypothesis | verdict | coefficient | p-value | observations | note |
| --- | --- | ---: | ---: | ---: | --- |
| `market_dynamism_entrepreneurial_entry_income_growth` | INCONCLUSIVE_DATA_PENDING | n/a | n/a | n/a | Missing WDI new-business-density treatment. |
| `market_dynamism_regulatory_freedom_hightech_exports` | SUPPORTED | +2.649 | 0.00503 | 463 | Regulatory freedom predicts higher high-tech export share. |
| `redistribution_transfer_work_incentive_lfpr_oecd` | PARTIAL | -0.01236 | 0.876 | 446 | Right-signed but not significant. |
| `redistribution_tax_transfer_mobility_oecd` | INCONCLUSIVE_DATA_PENDING | n/a | n/a | n/a | Only 12 observations after listwise deletion; needs mobility/SOCX repair. |
| `redistribution_gini_compression_median_income_growth_oecd` | REFUTED | -0.2394 | 0 | 709 | Gini-compression coefficient is opposite the registered positive-growth direction. |
| `redistribution_social_spending_bottom40_growth_panel` | PARTIAL | +0.000000 | 0.339 | 741 | Effect magnitude effectively zero. |
| `oecd_tax_wedge_low_wage_employment_penalty` | INCONCLUSIVE_DATA_PENDING | n/a | n/a | n/a | Missing low-education employment and inactivity outcomes. |
| `oecd_bargaining_extension_youth_entry_penalty` | PARTIAL | -0.03290 | 0.681 | 641 | Right-signed but not significant. |
| `business_freedom_employer_entry_employment_panel` | INCONCLUSIVE_DATA_PENDING | n/a | n/a | n/a | Treatment has no within-country variation under country fixed effects. |
| `temporary_contract_restrictions_youth_hiring_panel` | INCONCLUSIVE_DATA_PENDING | n/a | n/a | n/a | Missing OECD EPL temporary/permanent treatment aliases. |
| `oecd_taxben_benefit_cliff_lfp_penalty` | INCONCLUSIVE_DATA_PENDING | n/a | n/a | n/a | Missing TaxBEN participation-tax and EMTR treatment series. |
| `in_work_benefits_low_income_employment_panel` | INCONCLUSIVE_DATA_PENDING | n/a | n/a | n/a | Missing low-education employment, single-parent employment, and poverty outcomes. |
| `activation_sanctions_reemployment_duration_panel` | INCONCLUSIVE_DATA_PENDING | n/a | n/a | n/a | Missing job-search conditionality and sanction-rule treatment series. |
| `unconditional_transfer_work_hours_response_panel` | SUPPORTED | -0.000000265 | 0.0337 | 1,218 | Transfer proxy predicts lower employment-rate outcome under generic runner. |
| `state_trade_barriers_consumption_variety_panel` | PARTIAL | +0.000215 | 0.849 | 894 | Right-signed but not significant. |
| `rent_price_controls_building_permits_eu_panel` | INCONCLUSIVE_DATA_PENDING | n/a | n/a | n/a | Missing Eurostat building-permit and rent-burden outcomes. |
| `construction_permit_burden_housing_output_panel` | INCONCLUSIVE_DATA_PENDING | n/a | n/a | n/a | Missing WDI construction-output, urban-growth, and permit-burden series. |

## Cumulative 32-Spec Wave

Combining wave 1 and wave 2:

| Verdict | Count |
| --- | ---: |
| SUPPORTED | 4 |
| PARTIAL | 12 |
| REFUTED | 4 |
| INCONCLUSIVE_DATA_PENDING | 12 |
| Total | 32 |

The 32-spec wave is now fully triaged. The decisive generic-runner results are
not automatically scoreboard-ready; several specs use multi-outcome language,
constructed treatments, or broad proxies that need bespoke replication before
claim mapping.

## Best Follow-Up Targets

1. Promote the two supported market-process signals with secondary checks:
   `market_dynamism_government_consumption_investment_drag` and
   `market_dynamism_regulatory_freedom_hightech_exports`.
2. Repair the OECD TaxBEN / Benefits and Wages cluster, because it blocks five
   labour/welfare specs.
3. Repair the housing/construction Eurostat and WDI aliases, because the two
   housing specs are cleanly framed but data-pending.
4. Recheck the four refutations before mapping: they may be real evidence
   against broad market framings, or proxy/timing artifacts that need sharper
   treatments.
