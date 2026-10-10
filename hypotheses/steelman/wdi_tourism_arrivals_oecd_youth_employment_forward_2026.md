# Steelman: inbound arrival trips and next-year youth employment

## Measured claim

For the frozen country-year roster, a positive annual log change in international inbound arrival trips is expected to predict a positive change in the OECD 15–24 employment-to-population percentage from the same year to the next. The sign is fixed before outcome values or null masks are opened. A meaningful association is at least +1.0 percentage point per one-unit log change (about +0.10 percentage point for an approximately 10% arrival increase), with two-sided p ≤ 0.005 in this two-test family.

The strongest mechanism is that foreign visitor spending can increase demand for hospitality, retail, transport, and other services that often recruit younger workers. The WDI measure comes from UN Tourism and national administrative or survey collection. It counts arrival **trips**, not distinct travelers or visitor spending. The OECD outcome is a labour-force-survey ratio rather than a tourism statistic, so the variables are not mechanically identical.

## Strongest rival account

An improving economy, changing exchange rate, air-route expansion, security event, border rule, or one-off destination shock can affect both arrivals and youth jobs. Employment can begin responding before the next-year window. International arrivals omit domestic tourism. National series may count overnight tourists, all visitors including same-day and cruise visitors, air arrivals only, or accommodation guests; method and coverage vary. The WDI treatment `obs_status` field is blank throughout this vintage, so treatment-side breaks cannot be screened by a status flag. The hard |annual log change| ≤ 0.3 cap and residual-exposure concentration gates limit extreme leverage but cannot resolve undetected changes in visitor definition. Country and year fixed effects do not identify a tourism policy effect.

The five-year rule and complete/material floors are frozen before outcome access. OECD `OBS_STATUS=A` is required at both endpoints, excluding explicit `B` series breaks and unlabeled statuses.

## Relationship to prior IESET work

IESET already includes Singapore and UAE tourism-hub hypotheses and country-specific Dominican Republic and other tourism/development hypotheses. `oecd_youth_wage_gap_youth_employment` uses the same broad youth-employment outcome with another treatment. None is this exact international-arrival-growth → next-year youth-employment-change pair. The local Bonferroni correction covers only the two newly registered tests, not prior archive selection.

A `SUPPORTED` verdict would support only the measured descriptive association. `REFUTED`, `PARTIAL`, and `INCONCLUSIVE` remain publishable outcomes. No verdict earns causal, policy, school-score, or featured credit.

Sources: [World Bank tourism-arrivals definition and limitations](https://databank.worldbank.org/metadataglossary/world-development-indicators/series/ST.INT.ARVL); [OECD employment-rate definition](https://www.oecd.org/en/data/indicators/employment-rate.html).
