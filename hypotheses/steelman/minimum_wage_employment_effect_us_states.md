# Steelman — Minimum wage employment effects, US states

**The strongest argument against the "close to zero" prediction:**

The post-Card-Krueger consensus that minimum-wage employment effects are small relies heavily on research designs that look at modest wage hikes in tight labour markets, and then generalises to policy changes that now far exceed the historical range. The 2014-2024 wave of state and city minimum-wage increases has pushed some jurisdictions' minimums to 65-75% of state median wages — a range no prior study covers. Projecting zero-elasticity findings from the 1990-2010 literature onto the current policy environment conflates the historical parameter with the structural relationship.

Specific objections the hypothesis must engage with:

1. **The bite ratio matters and the spec does not condition on it.** A $0.50 increase in a state with median wages of $25 is a trivial intervention; the same nominal increase in Mississippi with a low median wage is a substantial one. Pooling all state-level hikes and estimating a single elasticity obscures the fact that the elasticity is probably non-linear in the minimum-to-median ratio. Cengiz-Dube-Lindner-Zipperer 2019 found zero effects at historical bite levels (~45-55% of median); the post-2014 Seattle, California, New York, DC minima test the 60-75% range where the theoretical monopsony case for small effects weakens. The v1 spec does not cleanly separate these regimes.

2. **Teen employment is not the only margin.** Employers faced with a binding minimum may respond on hours, scheduling, non-wage compensation (training, benefits), technology adoption (self-order kiosks, scheduling algorithms), or formalisation of previously informal arrangements (tipped work, off-the-books labour). A spec that only examines the E/P ratio misses most of the adjustment margins. The Seattle minimum-wage study (Jardim et al. 2017) found that while employment counts moved little, hours fell substantially — and the product of the two (labour earnings for affected workers) declined. A "close to zero" employment finding is compatible with meaningful aggregate harm on the hours margin.

3. **Publication bias in the border-discontinuity literature.** The Dube-Lester-Reich contiguous-county design is the gold-standard identification but has a known feature: it differences out any regional shock that moves both sides of the border equally, including industry-mix differences that are persistent but not time-invariant. Several careful meta-analyses (Neumark-Wascher 2007; Wolfson-Belman 2019) have argued the border-pair design systematically understates negative effects because minimum-wage hikes co-occur with regional business-cycle conditions the design does not fully absorb. The spec gets cleaner identification from the border design, but that cleanness may come at the cost of bias.

4. **Long-run vs short-run effects.** The Neumark-Wascher 2014 argument is that the employment margin takes 5-10 years to fully respond because firms adjust capital and location decisions slowly. A DiD design that averages 1-5 years post-treatment may find zero; extending to 10+ years may find larger negative effects. The v1 spec uses Callaway-Sant'Anna ATT averaging which does not by itself distinguish these horizons — the falsification rule should have pre-specified the horizon more narrowly.

5. **Regional heterogeneity matters and pooling hides it.** The 1992 Card-Krueger New Jersey finding is a tight-labour-market, eastern-seaboard case. The 2004 Neumark-Wascher response using different data and a different region found different results. Pooling all state-level hikes into a single ATT forces the framework to report one number when the true data-generating process plausibly differs by region and labour-market tightness. A heterogeneous effects specification (interacting treatment with state-level unemployment rate, industry mix, and bite ratio) would produce a more honest picture — and likely would reveal larger negative effects in loose-labour-market subsamples.

**How this steelman should shape the result card:**

The v1 result card must:

(a) Report the elasticity by bite-ratio quartile. If the "close to zero" finding collapses in the top bite-ratio quartile (>60% minimum-to-median), the framework must surface that and qualify the headline.

(b) Report an hours-adjusted earnings outcome alongside the employment count outcome. If employment is unchanged but hours fall meaningfully, the "minimum wage has no effect" headline is misleading and the framework must say so.

(c) Present the border-pair and state-panel elasticities side by side and note which produces the tighter CI. Where they disagree, the framework cannot adjudicate without stronger priors about which identification strategy is less biased — and should say so rather than picking one.

(d) Report short-run (1-3 year) and long-run (5-10 year) effects separately. If the sign changes across horizons, the pre-registered falsification rule needs a version bump.

The strongest version of the steelman argues the hypothesis is asking the wrong question: the interesting parameter is not "what is the elasticity averaged across all US state hikes 1990-2024" but "what is the elasticity as a function of bite ratio, regional tightness, and industry mix." A v2 heterogeneous-effects specification is the right follow-up and would plausibly overturn the "close to zero" finding for the post-2014 high-bite cohort.
