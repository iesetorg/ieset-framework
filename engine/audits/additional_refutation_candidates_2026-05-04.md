# Additional Refutation Candidates

Generated: 2026-05-04T19:50Z

Purpose: identify possible additional anti-intervention / pro-market refutation targets for human review. This file does not alter atlas links, school predictions, verdicts, or scores.

## Use Rule

Only promote a candidate after reviewing the target school's actual claim text and the hypothesis steelman. A supported market-compatible result is not automatically a refutation of Marxian, social-democratic, democratic-socialist, or Marxist-Leninist claims.

2026-05-04 hygiene note: the generic panel runner now respects stricter preregistered p-value thresholds. A scan after the fix found zero remaining `SUPPORTED`/`REFUTED` result cards with p-values above their own parsed alpha threshold.

## Cleanest Candidate Additions

These are the strongest candidates for explicit refutation-link review because the registered mechanism is closer to market allocation, property rights, competition, liberalisation, or price-stability claims.

| candidate | current verdict | why it is useful | promotion caveat |
|---|---|---|---|
| `frontier_tfp_market_liberal_panel_1970_2024` | PARTIAL, p=0.071 above preregistered p<=0.05 | Market-compatible regulation / competition / property-rights panel has the expected sign but misses its stricter registered threshold. | Do not count as a refutation win without robustness or a preregistered threshold revision. |
| `market_order_regulatory_quality_investment_share_panel` | SUPPORTED, p=0.0922 | Regulatory quality predicts investment share in a panel design. | Good anti-heavy-regulatory target; not a blanket anti-welfare-state claim. |
| `market_order_capital_account_openness_gdp_pc_growth_panel` | SUPPORTED, p=0.02 | Capital-account openness predicts faster GDP-per-capita growth in the preregistered panel. | Do not use against schools whose position is prudential sequencing rather than autarky. |
| `estonia_market_reform_30yr_income_convergence` | supported | Post-Soviet currency-board / flat-tax / privatisation / trade-liberalisation convergence case. | Strong anti-central-planning candidate; needs post-Soviet donor-pool steelman. |
| `ireland_market_opening_fdi_frontier_1987_2024` | supported | Trade openness, tax competitiveness, and FDI entry explain convergence better than classic industrial planning. | Use for market-opening vs planning, not as pure low-tax universal claim. |
| `ordo_anti_cartel_post_war_germany_economic_miracle` | supported | Price-control liberalisation plus anti-cartel competition order is a clean ordoliberal mechanism. | Refutes cartel/planning claims more cleanly than redistribution claims. |
| `china_post_wto_market_opening_vs_subsidy_tfp` | SUPPORTED | China TFP acceleration is tied more to WTO market opening than later subsidy-heavy intervention. | Stronger against central-planning/ML claims than against all industrial-policy claims. |
| `vietnam_doi_moi_private_sector_growth_share` | SUPPORTED, p=0.0568 | Doi Moi growth associated with private-sector entry, trade openness, and market reforms. | Treat as market reform inside one-party state; not a simple democracy/free-market case. |
| `milei_reforms_reduce_argentine_inflation` | SUPPORTED | Orthodoxy/stabilisation result against persistent inflation under fiscal dominance. | Best target is MMT/heterodox inflation claims, not broad Marxian theory. |
| `eu_regulatory_burden_productivity_drag` | SUPPORTED, p=0.082 | EU regulatory stack associated with productivity drag. | Needs careful treatment of confounding and Draghi-report-style competitiveness framing. |
| `eu_single_market_productivity_and_trade_gains` | SUPPORTED | Rules-based competition integration produced trade/productivity gains. | More ordoliberal than laissez-faire; can support market institutions plus supranational rules. |
| `trade_lib_trump_china_tariffs_2018_2024` | SUPPORTED | Tariffs reduced bilateral trade volumes. | Good anti-protectionism result; welfare-incidence and security externalities need steelman. |

## False Friends

Do not wire these as anti-left refutations without a new claim-specific rationale. They currently support, or can easily steelman, interventionist / Marxian / Minsky-style mechanisms.

- `financial_liberalisation_crisis_risk`
- `financial_deregulation_crisis_vulnerability`
- `banking_crisis_nordic_1991_1993_panel`
- `banking_crisis_laeven_valencia_predictors_panel`
- `gfc_endogenous_minsky_leverage_mechanism`
- `australia_2008_fiscal_stimulus_output_effect`
- `biden_ira_chips_fiscal_inflation_pass_through`
- `costa_rica_social_democratic_model_1980_2024`
- `japan_miti_success_then_stagnation_panel`

## Low-Rigor Expansion Pool

The `heritage_*_current_gap` and some `heritage_*_income_region_robustness` hypotheses are useful for breadth, but many are latest-year cross-sectional comparisons. They should not become decisive refutation wins unless upgraded to panel, event-study, or matched-country robustness designs.

## Highest-Leverage Repairs Still Needed

1. Minimum wage high-bite chain: fetch or construct `bls:LAU_state_teen_employment_population_ratio_panel`, `bls:OEWS_state_p10_hourly_wage_panel`, and `derived:minimum_wage_bite_ratio_subnational_panel`. The new QCEW restaurant/total panels are useful sector margins, but they do not satisfy the preregistered teen E/P or wage-percentile estimand.
2. GDPR / regulation target: OECD PMR is now fetched and resolved; remaining blockers are firm-level digital-sector scale/VC constructed panels and ISIC J employment share coverage.
3. Wealth tax target: construct tax-declaration exemption/undervaluation shares and clarify which OECD tax database flow is actually needed.
4. Nuclear phaseout target: add ENTSO-E reliability/price/fossil-capacity-factor data plus IEA/eurostat industrial electricity price coverage.
5. Rent-control and price-control chains: preserve city/region unit IDs; do not collapse these to country-year panels.
