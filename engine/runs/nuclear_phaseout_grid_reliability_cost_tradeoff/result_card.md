# Nuclear phase-out — grid reliability / cost trade-off

**Verdict:** inconclusive — Primary outcomes (industrial electricity price, wholesale day-ahead volatility, LOLE) require IEA / Eurostat NRG_PC_205 / ENTSO-E specialist fetchers that have not shipped. Testable surrogate (back-up reliance via fossil share of electricity): phase-out cohort fossil-share change -13.7pp vs retain cohort -18.2pp — gap +4.5pp (NOT consistent with +5.0pp threshold). Treatment is observed: phase-out cohort nuclear share fell from 41% to 24%; retain cohort held 40% to 34%.

## Summary

- The spec's PRIMARY outcomes are industrial electricity price, wholesale day-ahead volatility, fossil-fired back-up capacity factor, and loss-of-load expectation. The first two and the fourth are **not on disk** — the IEA / Eurostat NRG_PC_205 / ENTSO-E fetchers are pending. The headline tests cannot be run with publisher-pinned data; verdict is structurally **inconclusive**.
- The third primary (fossil back-up reliance) has an OWID-Ember surrogate: share-electricity-fossil-fuels. As a check on whether the testable piece points the way the spec predicts:

  - Phase-out cohort (DEU, BEL, CHE) fossil-share change 2005→2024: **-13.7pp**
  - Retain cohort (FRA, FIN, SWE, USA, GBR) fossil-share change 2005→2024: **-18.2pp**
  - Gap: **+4.5pp** (surrogate does NOT support the +5.0pp threshold)

- Treatment is verifiable: phase-out cohort nuclear-share declined materially while retain cohort held steady. See diagnostics.json for the country-level breakout.
- Renewables build-out: phase-out cohort +30.9pp, retain cohort +24.0pp — phase-out countries deployed renewables harder, partially substituting for the removed nuclear capacity (consistent with the spec's acknowledged collinearity).
- CO2-intensity of GDP: phase-out cohort -46.4%, retain cohort -46.1% — both decarbonising; phase-out cohort started higher and converged.

## Method

Period: 2005–2024. Phase-out cohort: DEU, BEL, CHE. Retain cohort: FRA, FIN, SWE, USA, GBR. Sensitivity cohort (excluded from primary cohorts): JPN, KOR.

**Why inconclusive, not refuted/supported:**

Per HYPOTHESIS_FRAMEWORK_AUDIT.md §E2, a method-valid failure (here: data gap on the headline outcomes) yields `inconclusive`, NOT `refuted`. Substituting a different series for industrial-electricity-price would violate provenance. The surrogate (fossil share) is reported as informative evidence only — it shares the spec's spirit on back-up reliance but does NOT settle the cost-of-electricity primary.

**Specialist fetchers needed for v2:**

- iea:industrial_electricity_price (band IC) — fetcher pending
- eurostat:NRG_PC_205 (industry electricity price) — series fetch pending
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
