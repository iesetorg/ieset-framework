# Nuclear phase-out — grid reliability / cost trade-off

**Verdict:** inconclusive — Primary outcomes (industrial electricity price, wholesale day-ahead volatility, LOLE) remain data-gated. Eurostat NRG_PC_205 is present locally but cannot satisfy the preregistered price leg without changing the cohort/period: Eurostat NRG_PC_205 has no selected-band rows for preregistered countries: CHE, USA; Eurostat NRG_PC_205 lacks full 2010-2024 selected-band coverage for: GBR (2021,2022,2023,2024). IEA industrial prices and ENTSO-E wholesale/adequacy data are not on disk. Testable surrogate (back-up reliance via fossil share of electricity): phase-out cohort fossil-share change -13.7pp vs retain cohort -18.2pp — gap +4.5pp (NOT consistent with +5.0pp threshold). Treatment is observed: phase-out cohort nuclear share fell from 41% to 24%; retain cohort held 40% to 34%.

## Summary

- The spec's PRIMARY outcomes are industrial electricity price, wholesale day-ahead volatility, fossil-fired back-up capacity factor, and loss-of-load expectation. Eurostat NRG_PC_205 is now on disk, but it does **not** cover the full preregistered industrial-price cohort/period. The IEA industrial-price and ENTSO-E wholesale/adequacy vintages are still absent, so the headline tests cannot be run without lowering the bar; verdict is structurally **inconclusive**.
- The third primary (fossil back-up reliance) has an OWID-Ember surrogate: share-electricity-fossil-fuels. As a check on whether the testable piece points the way the spec predicts:

  - Phase-out cohort (DEU, BEL, CHE) fossil-share change 2005→2024: **-13.7pp**
  - Retain cohort (FRA, FIN, SWE, USA, GBR) fossil-share change 2005→2024: **-18.2pp**
  - Gap: **+4.5pp** (surrogate does NOT support the +5.0pp threshold)

- Treatment is verifiable: phase-out cohort nuclear-share declined materially while retain cohort held steady. See diagnostics.json for the country-level breakout.
- Renewables build-out: phase-out cohort +30.9pp, retain cohort +24.0pp — phase-out countries deployed renewables harder, partially substituting for the removed nuclear capacity (consistent with the spec's acknowledged collinearity).
- CO2-intensity of GDP: phase-out cohort -46.4%, retain cohort -46.1% — both decarbonising; phase-out cohort started higher and converged.

## Blocker audit

Eurostat NRG_PC_205 coverage audit for the preregistered price leg (E7000, band MWH500-1999, I_TAX, EUR; required years 2010–2024):

| country | cohort | Eurostat geo | rows | first–last year | missing required years |
| --- | --- | --- | ---: | --- | --- |
| DEU | phaseout | DE | 38 | 2007-2025 | none |
| BEL | phaseout | BE | 37 | 2007-2025 | none |
| CHE | phaseout | CH | 0 | none | 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024 |
| FRA | retain | FR | 37 | 2007-2025 | none |
| FIN | retain | FI | 38 | 2007-2025 | none |
| SWE | retain | SE | 38 | 2007-2025 | none |
| USA | retain | US | 0 | none | 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024 |
| GBR | retain | UK | 27 | 2007-2020 | 2021, 2022, 2023, 2024 |

Primary blockers:

- Eurostat NRG_PC_205 has no selected-band rows for preregistered countries: CHE, USA.
- Eurostat NRG_PC_205 lacks full 2010-2024 selected-band coverage for: GBR (2021,2022,2023,2024).
- No local ENTSO-E/EPEX/Nord Pool day-ahead wholesale-price vintage exists.
- No local ENTSO-E/EIA fossil capacity-factor vintage exists; OWID fossil share remains an informative surrogate only.
- No local ENTSO-E MAF/NERC loss-of-load-expectation vintage exists.

## Method

Period: 2005–2024. Phase-out cohort: DEU, BEL, CHE. Retain cohort: FRA, FIN, SWE, USA, GBR. Sensitivity cohort (excluded from primary cohorts): JPN, KOR.

**Why inconclusive, not refuted/supported:**

Per HYPOTHESIS_FRAMEWORK_AUDIT.md §E2, a method-valid failure (here: data gap on the headline outcomes) yields `inconclusive`, NOT `refuted`. Substituting a different series for industrial-electricity-price would violate provenance. The surrogate (fossil share) is reported as informative evidence only — it shares the spec's spirit on back-up reliance but does NOT settle the cost-of-electricity primary.

**Specialist fetchers needed for v2:**

- iea:industrial_electricity_price (band IC) — no local vintage/manual drop on disk
- eurostat:nrg_pc_205 (industry electricity price) — local vintage present but incomplete for preregistered cohort/period; see diagnostics.primary_coverage_audit
- entsoe:day_ahead_wholesale_prices — fetcher pending
- entsoe:fossil_capacity_factor — fetcher pending
- entsoe:MAF_LOLE — fetcher pending

## Data

- owid:share-electricity-nuclear (Ember-derived; treatment verification)
- owid:share-electricity-fossil-fuels (Ember-derived; surrogate for back-up reliance)
- owid:share-electricity-renewables (Ember-derived; informative)
- owid:co2-intensity (informative)

## Caveats

- France's 2022 reactor-availability crisis (stress-corrosion cracking, ~half the fleet derated) confounds the FRA-as-control story for the gas-shock window. Steelman point #1.
- Gas-price shock 2022-2024 dominates any cost-outcome data and is geographically correlated with the phase-out cohort. Steelman point #2; the planned drop-2021-2024 sensitivity needs the missing price data.
- BEL extended Doel 4 / Tihange 3 beyond planned phase-out; CHE phase-out is passive. Treatment intensity is heterogeneous (steelman point #5).
- Safety / waste-management benefits — the actual reasons for phase-out — are unmeasured here. The hypothesis answers a narrow trade-off question, not a net-welfare question.
