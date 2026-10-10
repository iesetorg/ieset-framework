# Steelman: registrations and next-year youth employment

## Measured claim

For the frozen country-year roster, a positive annual log change in new limited-liability business registrations is expected to predict a positive change in the OECD 15–24 employment-to-population percentage from the same year to the next. The sign is fixed before the outcome values or null masks are opened. A meaningful association is at least +1.0 percentage point per one-unit log change (about +0.10 percentage point for an approximately 10% registration increase), with two-sided p ≤ 0.005 in this two-test family.

The plausible mechanism is that genuinely new firms can create entry-level vacancies and expand local demand for young workers. The WDI count is sourced chiefly from national business registries and is an observed administrative measure of **new formal limited-liability legal entities**, not a count of operating firms or jobs. The OECD outcome is a labour-force-survey employment ratio, not a registry statistic. This separation reduces mechanical overlap, though it does not identify a causal effect.

## Strongest rival account

Registrations and youth jobs can both rise with a general demand expansion, tax change, credit cycle, digital registry rollout, or a change in the legal preference for incorporation. Some registrations are restructurings, inactive entities, or tax vehicles. Informal firms and sole proprietors are omitted. Youth employment can affect expected profits and induce entry before the measured employment change. Country and year fixed effects remove stable country differences and common yearly shocks, but not country-specific demand shocks, anticipation, changing registry coverage, migration, demographic shifts, or changes in survey methods. WDI `obs_status` is blank in the pinned treatment vintage, so no treatment-side method-break screen is available.

The hard cap |annual log change| ≤ 0.4 and the postfit residual-exposure concentration gates reduce reliance on a few extraordinary records; they cannot certify comparability. The five-year rule and complete/material floors are fixed before outcome access. The exact OECD `OBS_STATUS=A` rule excludes explicit `B` series breaks and unlabeled statuses at both endpoints.

## Relationship to prior IESET work

`wdi_business_entry_rule_of_law_growth_panel` used registrations to study future GDP growth with an institutional interaction. `business_freedom_employer_entry_employment_panel` related regulatory scores to entry and working-age employment. `oecd_youth_wage_gap_youth_employment` used this outcome family with a wage-gap treatment. Those studies make this a related mechanism, though none is the exact registrations-growth → next-year youth-employment-change test. The family correction covers only the two newly registered tests; it does not erase archive-wide selection or earlier outcomes.

A `SUPPORTED` verdict would support only the preregistered descriptive association. `REFUTED`, `PARTIAL`, and `INCONCLUSIVE` are equally reportable. No verdict earns causal, policy, school-score, or featured credit.

Sources: [World Bank registration definition](https://databank.worldbank.org/metadataglossary/world-development-indicators/series/IC.BUS.NREG); [OECD employment-rate definition](https://www.oecd.org/en/data/indicators/employment-rate.html).
