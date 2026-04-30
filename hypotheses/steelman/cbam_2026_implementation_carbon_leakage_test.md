# Steelman — CBAM 2026 implementation carbon-leakage test

**The strongest arguments against the framework's "CBAM measurably re-routes high-carbon imports" framing:**

1. **The pre-CBAM leakage signature in EU trade data is small and contested.** Empirical work (Branger & Quirion 2014; Naegele & Zaklan 2019) found weak or null evidence of measurable carbon leakage in EU manufacturing imports during the EU ETS Phase II/III, with effect sizes <5% and rarely statistically significant. The leakage hypothesis is theoretically clean but empirically underwhelming for past data. If the pre-CBAM signature is small, the post-CBAM "reversal" is testing for a near-zero effect, which is hard to reject even with a working CBAM.

2. **Free allocation undermines the EU-side incentive structure CBAM is meant to replace.** EU producers in CBAM-covered sectors continue receiving free EU ETS allowances on a phase-out schedule running through 2034. As long as free allocation > 0, EU producers face only a fraction of the EU ETS price, so the carbon-cost differential between EU and import producers is smaller than the headline ETS price implies. CBAM importers face the full ETS-equivalent price; this is asymmetric protection that would distort trade in 2026-2034 even if leakage were zero. The hypothesis cannot cleanly distinguish leakage-correction from EU producer protection in this period.

3. **CBAM scope is narrow; the broader anti-leakage rationale lives outside scope.** CBAM 2026 covers cement, steel, aluminium, fertilisers, electricity, hydrogen — roughly 50% of EU ETS-emissions-weighted import exposure but a small share of EU manufacturing imports by value. Plastics, chemicals, glass, refined products, finished goods are out of scope. If leakage is occurring in those sectors, CBAM 2026 will not address it; testing CBAM-covered imports underrepresents the policy's stated objective.

4. **Carbon-intensity verification is weak; default values dominate.** During the 2023-2025 transitional phase, ~70% of CBAM declarations used default emission values rather than actual installation-level data, because exporter-side measurement capacity is limited. Default values reduce the carbon-intensity-gap precision; they also create incentives for exporters to remain on default (avoiding verification cost) rather than to actually decarbonise. The treatment-intensity variable (carbon-intensity gap) is contaminated by this measurement noise.

5. **Major exporters are aligning domestic carbon-pricing to neutralise CBAM rather than redirect trade.** China launched its national ETS in 2021 and broadened it 2024; Turkey announced an ETS for 2026; India is exploring carbon-credit trading scheme. If exporter-country domestic carbon prices rise to CBAM-equivalent levels, CBAM costs are netted against domestic carbon-tax credits and the trade-flow effect attenuates. This is the policy's stated objective (push global carbon-pricing alignment) but it means the hypothesis's trade-redirection test will measure a smaller-than-headline effect even if the policy "works" in its broader sense.

6. **Demand-destruction in covered sectors confounds the test.** EU cement and steel demand is structurally weak post-2022 (construction slowdown, automotive electrification); CBAM-covered import volumes will fall partly because EU demand is falling. Coding the volume decline as "CBAM-induced redirection" overstates the policy effect. The correct counterfactual requires netting out cyclical EU demand, which is hard at the product-month level.

**How this should shape the v1 result card when run:**

- Report the pre-CBAM leakage signature as a separate first-stage finding. If it is null, the post-CBAM re-routing test is a null-by-construction.
- Net out free-allocation distortion when computing carbon-cost differential. The effective ETS-price faced by EU producers ≠ headline ETS price.
- Acknowledge scope-narrowness: CBAM-covered products are not the full leakage frontier.
- Treat default-value declarations separately from verified-emissions declarations in the gap-treatment regression. Different signal strength.
- Flag the exporter-country domestic-carbon-pricing alignment as an explicit confounder; report results with and without controlling for it.
- Net out cyclical EU demand using non-CBAM control products (similar HS but outside scope).
- Climate-effectiveness of CBAM (global emissions reduction) is out-of-frame; do not over-interpret a trade-flow null as a climate-policy verdict.
