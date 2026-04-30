# Steelman — EU gas storage winter 2022-2023 demand destruction vs substitution

**The strongest arguments against the framework's "EU 15% gas cut decomposes cleanly into four measurable channels" framing:**

1. **Weather did most of the work, and the policy contribution is hard to isolate.** Both the 2022-2023 and 2023-2024 winters were unusually warm (HDD anomaly -10 to -15% vs 2017-2021 mean across central Europe). Bruegel's December 2022 decomposition attributed roughly 60% of the cut to weather. If weather is dominant, the policy + behavioural response is a smaller residual than headline numbers suggest, and the decomposition is sensitive to weather-normalisation methodology. Different HDD-specifications (degree-day base 18°C vs 15.5°C, threshold vs linear) flip the share substantially.

2. **The industrial-destruction-vs-efficiency split is empirically near-impossible to identify cleanly.** Industrial gas use fell, and industrial output also fell — but the elasticity that would let us back out "destruction vs efficiency" is itself shock-period-specific. Plants ran at lower utilisation rates without permanent closure; some shifted to non-gas energy inputs (electrification of process heat); some imported intermediates rather than producing domestically. The "structural capacity loss" share that the hypothesis tries to identify is not separable from temporary utilisation cuts in 2022-2023 data; only late-2024 / 2025 reading of capacity counts can settle it.

3. **The hidden-imports problem is large.** Ammonia, urea, hot-rolled steel, aluminium imports into the EU rose substantially 2022-2023; this is gas demand "saved" inside the EU but appearing as gas demand in producing countries (Egypt, Saudi Arabia, USA). A true global gas-balance figure shows the EU outsourced rather than reduced; the headline 15% number is misleading at climate-policy scale. The hypothesis's "hidden-flow problem" caveat acknowledges this but the channel cannot be measured without UN Comtrade reweighting that the v1 design does not include.

4. **Coal-restart as a fuel-switching channel was politically embarrassing and partially reversed by 2024.** Several EU countries restarted coal plants for winter 2022-2023 (DEU lignite, NLD coal, AUT, ITA), then reduced coal output in 2023-2024 as gas refilled. Coding "fuel-switching" as a stable channel mistakes a one-winter regression for a sustained substitution. The decomposition needs to flag that this channel partially reversed.

5. **Residential conservation may not be sustainable.** Households cut thermostat settings and gas-boiler use under high prices; as TTF prices fell from €300/MWh to €25-40/MWh through 2023-2024, residential gas use partially rebounded. The "conservation" channel is price-elastic, not policy-induced; it does not represent durable demand reduction. A permanent-conservation interpretation overstates the policy lesson.

6. **Decomposition assumes channels are independent; they are not.** If industrial output falls (channel a), this reduces electricity demand (channel c), which reduces power-sector gas use (channel c again). Conservation (channel d) and warm weather (residual) interact: people are less likely to lower thermostats further when it is already warm. Treating the four channels as additive overcounts in some cells and undercounts in others; the true decomposition is non-linear and depends on the order in which channels are netted out.

**How this should shape the v1 result card when run:**

- Report channel shares with uncertainty bands, not point estimates. The decomposition has wide error bars.
- Run the second-winter (2023-2024) test prominently — it is the cleanest weather-vs-policy isolation.
- Report the hidden-imports adjustment as a separate sensitivity. EU gas demand "saved" minus embedded energy in imported intermediates is the climate-relevant number.
- Flag coal-restart as a temporary, partially-reversed channel; do not code it as substitution.
- Note that residential conservation reverses as prices fall; durable-policy interpretation is unsupported.
- Acknowledge non-independence of channels; the additive decomposition is an approximation.
