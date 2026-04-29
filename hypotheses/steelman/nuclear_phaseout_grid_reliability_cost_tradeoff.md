# Steelman — Nuclear phase-out grid reliability cost trade-off

**The strongest arguments against the framework's "nuclear phase-outs raised industrial cost and degraded grid reliability" framing:**

1. **France's 2022 nuclear availability crisis undercuts the clean "nuclear-retaining equals low-cost" story.** France had to derate nearly half its reactor fleet in summer 2022 due to stress corrosion cracking, importing electricity from neighbours and at points setting record wholesale prices. The comparison of "phase-out countries vs nuclear-retaining countries" is cleaner in theory than in practice when the canonical nuclear-retainer is simultaneously experiencing a large availability shock. Any panel that codes FRA as control-untreated for 2022 must handle the availability shock carefully or the DiD is mis-identified.

2. **Gas-price shock 2022-2024 dominates post-2020 cost data and no DiD design can fully neutralise it.** Phase-out countries happen to be gas-indexed-market countries (Germany, Belgium, Switzerland); retaining countries include France with less gas exposure and USA with domestic shale. The treatment and the gas-shock exposure are correlated by geography / policy history. Attributing 2022-2024 price divergence to "phase-out policy" rather than "gas-shock geography" requires tighter identification than the design provides. The pre-registered drop-2021-2024 sensitivity is essential, and the writeup must take seriously the possibility that the effect collapses there.

3. **Safety and waste-management benefits are unmeasured.** Phase-out countries chose their policy after weighing Fukushima (2011), Chernobyl legacy, and national waste-repository challenges. These are legitimate welfare considerations that the hypothesis does not measure. A finding that phase-outs raised industrial electricity costs, even if robust, says nothing about whether the policy is net-welfare-positive once safety and waste considerations are included. The writeup must flag this explicitly — the hypothesis answers a narrow question, not the policy question.

4. **Renewables build-out partially substituted for nuclear capacity.** Germany deployed massive wind and solar through the phase-out period; the nuclear capacity is no longer on the grid, but clean capacity replaced it. The treatment effect of "nuclear phase-out" inherently controls for renewables build-out via the collinearity between phase-out and build-out. The net effect of "phase-out plus build-out" may be cost-increasing, but the counterfactual of "retain nuclear AND also build renewables" (which FRA is trying to do) is a different policy, and no country has tested both simultaneously at scale. The comparison is unavoidably ambiguous.

5. **Belgian and Swiss phase-outs are partial and delayed.** Belgium extended two reactors (Doel 4, Tihange 3) beyond planned phase-out; Switzerland's phase-out is passive (no new build) rather than active closure. Coding these as "treated" similarly to Germany elides a large difference in implementation. The treatment variable heterogeneity is real, and pooled effects risk misleading.

6. **Loss-of-load-expectation data are not consistently reported.** Cross-country reliability comparisons are intrinsically difficult because reserve-adequacy methodologies differ (ENTSO-E MAF vs NERC vs national operator methods). The "reliability" outcome is the weakest measured in the hypothesis, and any strong statement about phase-out-induced reliability degradation will rest on thin evidence. Be cautious.

7. **The alternative counterfactual (keep nuclear indefinitely at high cost) is not costless.** European nuclear fleets are aging; maintenance costs are rising; new-build economics (Hinkley Point C, Flamanville 3, Olkiluoto 3) have been poor. A phase-out that happened to coincide with a period when life-extension or new-build would have been expensive may be cheaper than the naive comparison implies. The policy-counterfactual should include the realistic cost of extending or replacing aging reactors, not an idealised "nuclear stayed the same."

**How this should shape the v1 result card when run:**

- Report the pre-2020 sample separately from the gas-shock-affected post-2020 sample. If the effect is only visible in the gas-shock window, the interpretation is different.
- Handle France's 2022 availability shock with an explicit dummy or sensitivity dropping FR for that year.
- Acknowledge safety and waste trade-offs explicitly as unmeasured. The headline finding is narrow.
- Report continuous-treatment (nuclear share change) alongside binary phase-out-legislated. The binary treatment is coarse; continuous captures the gradual nature of actual phase-outs.
- Distinguish DEU (executed phase-out) from BEL (delayed / partial) from CHE (passive). Pooled effects mask different treatment intensities.
- Frame the actionable implication as grid-design — retain firm dispatchable capacity until equivalent replacement exists — rather than as "retain nuclear forever" or "phase-out was wrong." Countries that legislated phase-outs cannot unmake 15 years of policy commitment; the relevant policy lesson is about sequencing.
- Be humble about magnitude. Even under favourable specifications, the phase-out-attributable share of total cost divergence is plausibly 20-40%, with gas-shock and secular trends doing much of the work.
