# Steelman — EU ETS price 2022-2026 carbon-signal strength

**The strongest arguments against the framework's "ETS price step-change accelerated emissions reductions" framing:**

1. **Free allocation blunts the effective price for EU producers in covered sectors.** EU ETS Phase 4 (2021-2030) continued free allocation to CBAM-covered industrial sectors (cement, steel, aluminium, fertilisers, chemicals) on a phase-out schedule running through 2034. EU producers in these sectors face only a fraction of the headline EUA price; the binding marginal cost is closer to €20-40/tCO2 effective rather than €70-100/tCO2 nominal. Treating the headline price as the signal overstates what producers actually faced; this also explains why industry abatement capex is slower than power-sector response.

2. **Power-sector emissions decline is dominated by coal phase-out POLICIES, not ETS price.** Germany legislated coal phase-out by 2038 (later accelerated discussions to 2030); UK closed last coal plant 2024 (post-Brexit, outside EU ETS); Italy, Spain, Netherlands closed coal capacity on policy schedules independent of ETS price. Crediting ETS price with coal-to-renewables transition mistakes a coincident-policy outcome for a price-induced one. The right counterfactual is "ETS at €30 with policy phase-out" vs "ETS at €80 with policy phase-out" — the marginal effect of price is small once policy is in place.

3. **2022-2024 emissions decline is dominated by gas-shock industrial contraction, not abatement.** The 2022 gas shock idled energy-intensive industrial output (chemicals, fertiliser, glass, ceramics); ETS-covered emissions fell because activity fell, not because intensity fell at constant activity. The hypothesis tries to net this out by using intensity (emissions/output) but the output measure is noisy at country-sector level, and the intensity metric inherits this noise. A meaningful share of the headline ETS-emission-decline is just less production.

4. **The EUA price-signal is pro-cyclical and may unwind.** EUA price fell from peak €105 (Feb 2023) to €60-70 range (2024) and €50-60 (2025) as industrial production weakened and Phase 4 Market Stability Reserve over-supply released allowances. If the price falls further, the "signal strength" measured 2022-2024 is a transient peak rather than sustained step-change. The hypothesis windows 2022-2026; the v1 reading may be flattering relative to a 2026-2030 retrospective.

5. **Coal-to-gas substitution in power was BLOCKED by 2022 gas shock — perverse outcome.** ETS price + classical theory predicts coal-to-gas fuel-switching at €40+ EUA price. In 2022-2023, the gas-shock raised gas prices so high that some EU power systems ran MORE coal than they would have under normal gas prices, despite the high EUA price. The signal was overwhelmed by the gas-shock counter-signal in the power sector during exactly the window the hypothesis tests. The "price signal works" framing is undermined by this episode.

6. **Industrial abatement capex announcements ≠ realised abatement.** Hydrogen + electrification + CCS announcement counts rose post-2021, but realised projects have been delayed or cancelled (most prominently Salzgitter SALCOS, ArcelorMittal hydrogen plans postponed, multiple CCS projects). Coding announcements as "capex elasticity to ETS price" overstates the policy response; realised abatement is much smaller. The hypothesis flag this in limitation (4) but the empirical test relies on announcement data because realised data lags.

**How this should shape the v1 result card when run:**

- Decompose effective vs headline EUA price. EU producers in CBAM-covered sectors face a much smaller effective price; the regression should be on effective.
- Disentangle policy-driven coal-phase-out from price-driven coal-to-gas. Use country-policy-timeline interaction.
- Report power-sector and industry-sector results separately. Power has a real fuel-switching signal; industry is much slower and contested.
- Acknowledge gas-shock counter-signal in 2022-2023 power sector explicitly.
- Distinguish announced from realised abatement capex. Announcements are leading; realised is the binding test.
- Treat the post-2024 EUA-price decline as a sensitivity case — re-run with the full 2022-2026 window and a 2022-2024-only window.
- Climate-effectiveness-of-ETS framing is downstream and out-of-frame for this hypothesis; we are testing one piece (price-signal strength).
