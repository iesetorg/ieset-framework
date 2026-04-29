# Steelman — Nordic outcome persistence decomposition

**The strongest argument against the framework's decomposition-explains-the-gap framing:**

Nordic outcomes are irreducibly cultural and historical, and the attempt to decompose them into transferable institutional features will systematically miss the binding constraint. Government effectiveness scores are downstream of the outcomes they're being used to explain, not upstream of them. The decomposition conflates the outcome with its own proxy, then congratulates the framework for the tautology.

Specific objections the hypothesis must engage with:

1. **Endogeneity of institutional-quality indices.** WGI Government Effectiveness is built partly from surveys that ask respondents about perceived government performance — which is itself shaped by the outcomes the index is supposed to predict. Nordic scores high because Nordic outcomes are high; using WGI GE as an explanator of Nordic outcomes is partly a circular exercise. The decomposition would look strong even if no causal mechanism were operating.

2. **Country fixed effects absorb the interesting variation.** The hypothesis decomposes the Nordic-vs-Southern-Europe gap *with country FE in the specification*. Country FE soak up every time-invariant Nordic feature (social trust, small homogeneous populations, Protestant work ethic traditions, flexicurity institutions, the Norwegian SWF itself) along with every time-invariant confounder. What's left is within-country variation over 1996 – 2023 — a period in which almost nothing structural about any of these societies changed. The decomposition may look clean only because country FE have done the work and the channels are explaining residual noise.

3. **The comparator set is selected.** Southern Europe (ESP, ITA, GRC, PRT, FRA) shares euro-zone membership, Mediterranean legal traditions, later industrialisation, and weaker state capacity. But so do many Latin American countries that also tried Nordic-style welfare expansion and failed. If the comparator set were Switzerland, Netherlands, Germany — high-institutional-quality high-outcome non-Nordic peers — the Nordic-specific effect would shrink or disappear, and the decomposition's story would be different. Sample choice partly determines the finding.

4. **The "residual collapsing" falsification is under-constrained.** A 30% threshold for the primary outcome is defensible but arbitrary. Alternative thresholds (20%, 40%) produce qualitatively different conclusions. The pre-registration pins a number, which is good, but the hypothesis is one robustness-specification away from a different answer — and without the v2 channels (labour flex, social trust), the v1 finding has limited generalisation value.

5. **Reverse causation on fiscal discipline.** Low debt-to-GDP is being used as an explanator of good outcomes, but good outcomes produce the tax receipts and political slack that permit low debt. The causal arrow plausibly runs from good governance/good economy → low debt, not from low debt → good outcomes. Including debt/GDP as a channel may be measuring the same thing as the outcome.

**How this steelman should shape the result card:**

The v1 result card must:

(a) Report the raw Nordic-Southern Europe gap *without* country FE alongside the with-country-FE specification, so readers see how much of the raw gap country FE absorb before the channels do anything.

(b) Run the same specification on an alternative comparator set (NLD, CHE, DEU, AUT, BEL) and report whether the Nordic-dummy coefficient changes substantially. If yes, the "Nordic-specific effect" claim is sample-dependent.

(c) Acknowledge WGI endogeneity openly; supplement with an institutional-quality index that has less survey-of-outcomes exposure (V-Dem administrative-process indicators, when the fetcher ships).

(d) Report both the within-country residual and the between-country residual separately, so the claim "channels explain the gap" is disciplined against the country-FE-does-the-work objection.

The steelman's strongest version points at a v3 research agenda: decompose the Nordic-specific country fixed effect itself into time-invariant institutional features that cannot be measured in a panel. That's a different methodology (historical / cross-sectional, not panel) and the framework should note the boundary.
