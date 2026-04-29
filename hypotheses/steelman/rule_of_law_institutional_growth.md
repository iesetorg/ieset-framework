# Steelman — Rule of law and institutional growth

**The strongest argument against this hypothesis:**

The institutions-growth correlation is real; the causal interpretation is unidentified. WGI Rule of Law is constructed from surveys that measure perceptions of rule-of-law conditions, and those perceptions are themselves shaped by economic outcomes. Rich countries get good scores because they are rich and visible; poor countries get poor scores partly because they are poor. A regression of growth on WGI RL with country fixed effects is less polluted than a cross-sectional one but still captures the mutual co-evolution of outcomes and perceptions. The Acemoglu-Johnson-Robinson settler-mortality instrument was an attempt to escape this problem; Albouy 2012 and subsequent critiques have cast serious doubt on that instrument's validity. No fully clean identification of the rule-of-law-to-growth causal channel exists in the published literature.

Specific objections the hypothesis must engage with:

1. **WGI construction endogeneity.** WGI RL is built from roughly 20 underlying sources, several of which are business-climate surveys (Heritage Foundation, Fraser Institute, business executive opinion polls) whose respondents are reporting perceptions conditioned on observable economic performance. A country with strong growth will be perceived as having better rule of law even if its legal institutions are unchanged; a country in recession will be perceived as having worse rule of law. The cross-sectional correlation between RL and growth is partly mechanical; the within-country panel correlation is less so but still non-zero for this reason.

2. **Glaeser-La Porta-Lopez-de-Silanes-Shleifer 2004: human capital comes first.** Their argument is that autocratic regimes with educated populations (Korea under Park, Taiwan under Chiang, Singapore under Lee Kuan Yew) developed economically and then developed rule-of-law institutions, not the other way around. The causal primacy of human capital over institutions produces the same cross-country correlation as the institutions-first story but implies very different policy conclusions. The v1 spec includes secondary school enrolment as a control but it enters as a control, not as a competing causal variable; the two stories are not adjudicated.

3. **Fixed effects do too much work and too little work.** Country fixed effects absorb time-invariant institutional factors (legal origin, colonial history, geography), which is the right thing to do for bias. But they also absorb the variance the cross-sectional literature was identifying off of. The remaining within-country variation in WGI RL is small (WGI scores change slowly) and dominated by measurement noise. The panel coefficient is identified off noisy changes in a slow-moving composite, and is likely biased toward zero by attenuation — making the panel finding conservative but weak.

4. **Reverse causation via tax base.** Growing economies can afford better courts, pay judges competitive wages, fund anti-corruption agencies, and invest in legal-training infrastructure. Stagnant economies cannot. The rule-of-law-to-growth relationship may therefore run primarily backward, with rule-of-law improvements being funded by prior growth rather than causing subsequent growth. The panel-FE spec does not resolve this because it uses contemporaneous or lagged RL against future growth, and contemporary RL reflects prior growth's cumulative effect on state capacity.

5. **Heterogeneous effects by development level.** The institutions-growth relationship is plausibly strong for countries below a certain GDP threshold (where predation, weak property rights, and contract unenforceability are binding constraints) and weak for countries above it (where rule-of-law is high enough that marginal improvements do not shift investment decisions). A pooled linear specification misses this. The coefficient reported in the headline will be a weighted average of a strong effect in developing countries and a near-zero effect in advanced economies, and will not represent the data-generating process for either group cleanly.

**How this steelman should shape the result card:**

The v1 result card must:

(a) Report the panel-FE coefficient alongside the pure cross-sectional coefficient, and report both RL-only and RL-plus-GE specifications. If the RL coefficient is driven entirely by the non-GE component or vanishes in the panel, the framework cannot claim a clean rule-of-law-specific effect.

(b) Report results for low-income (initial GDP pc < $5000 PPP), middle-income, and high-income subsamples. If the effect is only present in the low-income subsample, the headline claim should be narrowed accordingly.

(c) Acknowledge the WGI construction endogeneity openly and report a robustness spec using a single upstream source (V-Dem judicial-independence component, or WJP when the fetcher ships) whose construction has less output-variable exposure.

(d) Note that the spec does not identify a causal arrow and present the relationship as associational, with the causal interpretation pending a v2 that exploits natural-experiment variation.

The strongest version of the steelman argues the hypothesis as stated cannot escape the causal-direction problem at all — it can only report the joint co-movement and leave causal interpretation to the reader. A v2 would need either a plausibly-exogenous institutional-quality shock (post-colonial independence, post-communist transition, judicial-reform events) or a geographic-instrument strategy that addresses the Albouy critique.
