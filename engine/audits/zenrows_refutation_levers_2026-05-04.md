# ZenRows/Data Fetch Refutation Lever Audit

Generated: 2026-05-04

Purpose: inventory the data landed during the same-day ZenRows/data-unblocking push and identify which registered hypotheses can legitimately test claims against Marxian, Marxist-Leninist, democratic-socialist, and social-democratic positions without bending the framework.

## Landed Data

| Source | Rows | Period | Transport | Main affected hypothesis cluster |
|---|---:|---|---|---|
| `us_census:spm_child_poverty_rate` | 15 | 2009-2023 | direct | Biden CTC child poverty |
| `irena:installed_capacity_renewable` | 5,848 | 2000-2025 | direct | renewables industrial policy |
| `irena:installed_capacity_solar_pv` | 4,237 | 2000-2025 | direct | renewables industrial policy |
| `irena:installed_capacity_wind` | 3,091 | 2000-2025 | direct | renewables industrial policy |
| `owid:intergenerational-earnings-elasticity` | 12 | 2013 | direct | intergenerational mobility |
| `usdol:state_minimum_wage_history` | 2,106 | 1968-2024 | direct | minimum-wage state/subnational cluster |
| `oecd:OECD.ELS.HD_DSD_HH_DASH_DF_HSG_INEQ_1.0` | 1,235 | 2004-2025 | `zenrows` | OECD housing/income segregation channel |
| `laeven_valencia:banking_crisis_indicator` | local vintage | crisis panel | direct/manual | financial crisis risk |
| `laeven_valencia:currency_crisis_indicator` | local vintage | crisis panel | direct/manual | financial crisis risk |
| `laeven_valencia:peak_to_trough_gdp_loss_crisis_years` | local vintage | crisis panel | direct/manual | financial crisis severity |

## Clean Refutation Levers

### 1. Minimum-Wage High-Bite Cluster

Best target for Marxian/social-democratic refutation if data repairs land.

Registered hypotheses:
- `minimum_wage_above_median_employment_teen_effects`
- `minimum_wage_disemployment_at_high_bite_ratios`

Why it is clean:
- `minimum_wage_above_median_employment_teen_effects` marks Marxian, democratic-socialist, Marxist-Leninist, and social-democratic predictions as `falsified`.
- `minimum_wage_disemployment_at_high_bite_ratios` marks Marxian, democratic-socialist, and Marxist-Leninist predictions as `falsified`.
- The claim is not a cheap first-order "minimum wages bad" claim. It explicitly grants first-order wage gains and tests the second/third-order employment, NEET, and bite-ratio channels.

Current landed data:
- `usdol:state_minimum_wage_history` is now present and loaded in the minimum-wage diagnostics.

Binding missing data:
- `bls:LAU_state_teen_employment_population_ratio_panel`
- `bls:OEWS_state_p10_hourly_wage_panel`
- `bls:OES_state_median_hourly_wage_panel`
- `derived:minimum_wage_bite_ratio_subnational_panel`

In-flight note:
- `data/fetchers/bls.py` currently has an uncommitted QCEW state-panel implementation from the data-unblocking work. It can help `federal_minimum_wage_employment_meta`, but it does not yet land the LAU teen E/P or OEWS/OES median/p10 wage panels required for the strongest refutation tests.

Next repair:
- Preserve state/county `unit_id`; do not collapse to `USA,year`.
- Build LAU/CPS state teen E/P, OEWS/OES median and p10 wages, then derive the state-year bite ratio from USDOL statutory floors.

### 2. Wealth-Tax Capital Flight / Revenue-Yield Gap

Best fiscal refutation target.

Registered hypothesis:
- `wealth_tax_capital_flight_revenue_yield_gap`

Why it is clean:
- Marxian, democratic-socialist, Marxist-Leninist, and social-democratic predictions are registered as `falsified`.
- The hypothesis grants first-order revenue collection and tests whether the second/third-order channels appear: HNW migration, base erosion, asset reshuffling, and below-forecast yield.

Current landed data:
- No decisive new same-day vintage lands the required wealth-tax panel.

Binding missing data:
- France ISF/IFI realized revenue and official forecast vintages.
- Norway 2022 wealth-tax hike realized revenue plus migration/outflow measures.
- Colombia patrimonio 2022-2023 realized/forecast panel.
- Spain grandes fortunas realized/forecast panel.

Next repair:
- Hand-curate a public-finance panel with row-level `source_url`, `forecast_vintage_year`, `revenue_year`, forecast, realization, currency, and case id.
- Do not rerun from Norway-only or broad WDI proxy data.

### 3. Intergenerational Mobility Institutional Channels

Important but not a clean refutation of social democracy.

Registered hypothesis:
- `intergenerational_mobility_cross_country`

Current landed data:
- `owid:intergenerational-earnings-elasticity`
- `oecd:OECD.ELS.HD_DSD_HH_DASH_DF_HSG_INEQ_1.0` via ZenRows

Why it matters:
- It can test whether mobility is better explained by education, residential segregation, and housing affordability than by redistribution level alone.
- That is useful for attacking crude transfer-only narratives.

Why it is not a clean anti-social-democratic win:
- Social-democratic prediction is registered as `supported`.
- Marxian prediction is registered as `mixed`.

Binding missing data:
- `oecd:OECD.EDU.IMEP_DSD_EAG_FIN_DF_FIN_RESOURCES_1.0`
- `owid:share-of-children-in-the-bottom-quintile-who-make-it-to-the-top-quintile` as robustness
- bespoke partial-R2 / leave-one-out replication branch

## False Friends

These landed data improve the framework, but should not be pitched as refuting Marxian/social-democratic claims under the current registrations.

| Hypothesis | Current direction | Why not use as anti-left leverage |
|---|---|---|
| `tax_inequality_biden_ctc_2021_child_poverty` | `SUPPORTED` | Supports social-democratic/Marxian redistribution predictions. |
| `financial_liberalisation_crisis_risk` | `SUPPORTED` | Supports Marxian/democratic-socialist financial-instability predictions. |
| `china_renewables_industrial_policy_learning_curve` | `INCONCLUSIVE_DATA_PENDING` | If LCOE lands and learning-curve effects hold, current links likely support industrial-policy/eco-socialist/Marxian claims. |

## Current Score-Direction Snapshot

Across all current linked/run hypotheses, not only the new data wave:

| School | Refuted by current run directions | Supported by current run directions | Pending/neutral |
|---|---:|---:|---:|
| `marxian` | 24 | 23 | 87 |
| `social_democratic` | 22 | 22 | 89 |
| `democratic_socialist` | 24 | 22 | 91 |
| `marxist_leninist` | 21 | 22 | 92 |

Interpretation: the framework is currently balanced enough that cherry-picking "anti-left" wins would be visible. The highest-integrity path is to unblock the clean preregistered mechanisms above and let verdicts fall where they fall.

## Recommended Attack Order

1. Finish the minimum-wage data bundle: LAU/CPS teen E/P, OEWS/OES p10 and median wages, derived bite ratios.
2. Run the two clean high-bite minimum-wage hypotheses only after unit coverage passes.
3. Build the wealth-tax realized-vs-forecast panel, starting with France because the current run explicitly fails on `FRA not in panel`.
4. Complete OECD education-spending inequality and rerun intergenerational mobility as an institutional-channel test, not as a direct social-democratic refutation.
5. Keep CTC, Laeven-Valencia, and China renewables in the honest-result bucket even where they help opposing schools.
