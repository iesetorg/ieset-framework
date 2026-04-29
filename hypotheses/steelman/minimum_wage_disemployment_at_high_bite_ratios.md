# Steelman — Minimum-wage disemployment at high bite ratios

**The strongest argument against this hypothesis:**

The Card-Krueger 1994 / Dube-Lester-Reich 2010 / Cengiz-Dube-Lindner-Zipperer 2019 line of argument is that the post-1990 US-state and border-county evidence does NOT show measurable teen disemployment even at relatively high bite ratios, and that the Chicago "bite-ratio terciles produce visible cross-cohort divergence" framing was decisively undermined once researchers controlled for the regional cyclical confounders that the Neumark-Wascher national-panel specification absorbed into the treatment effect. The empirical content of the bite-ratio claim — that high-bite cohorts should look measurably worse than low-bite cohorts on teen E/P — has been tested repeatedly and the cross-cohort differential is statistically indistinguishable from zero in the modern literature, including at bite ratios well above the 0.55 cutoff this spec uses.

Specific objections the hypothesis must engage with:

1. **Monopsony in low-wage labour markets neutralises the bite-ratio prediction.** If concentrated employers face upward-sloping labour supply curves (Manning 2003, Azar-Marinescu-Steinbaum-Taska 2020), modest minimum-wage increases above the competitive equilibrium can increase employment, not reduce it. The bite-ratio framing assumes a competitive labour market; if monopsony is empirically common in the affected segments (food service, retail, accommodation), the cross-cohort differential could be near zero or even positive without falsifying the broader monopsony story. A spec that treats the differential as a direct test of "minimum-wage effects" conflates the competitive-market and monopsony-market predictions.

2. **Selection of which states become high-bite is endogenous.** States with low median wages (Mississippi, Arkansas) mechanically have higher bite ratios at the federal floor than states with high median wages (Massachusetts, California) at much higher state floors. The HIGH-BITE cohort is therefore systematically composed of low-productivity Southern states with structurally weaker teen labour markets for unrelated reasons (school enrolment, demographic composition, agricultural seasonality). The cross-cohort differential confounds the bite-ratio effect with the South/non-South productivity gap. A spec that does not absorb state-fixed-effects WITHIN the cohort assignment (or use a within-state bite-ratio variation design) will recover a biased estimate.

3. **The 2019 Cengiz-Dube-Lindner-Zipperer bunching design is the modern gold standard and finds null effects on hours-worked at affected wage cells.** The bunching estimator directly tests whether jobs at the affected wage range disappear post-hike. Across 138 state-level minimum-wage events 1979-2016, the missing-jobs count is statistically zero even for hikes with bite ratios well above 0.55. The Chicago-direction prediction has been falsified at the level of jobs, not just employment ratios. The spec's stratified-DiD design is less powerful than bunching and may confirm the Chicago claim at lower confidence than the bunching evidence rejects it.

4. **Teen E/P trends are dominated by school-enrolment dynamics, not minimum-wage shocks.** Teen labour-force participation has fallen ~20pp since 1990 driven primarily by rising college enrolment and changing parental expectations about teen work. Any specification that uses teen E/P as the outcome must control for state-by-year variation in school enrolment; otherwise the cross-cohort differential is confounded with cohort differences in education trends. The Chicago framing implicitly attributes teen-E/P decline to minimum wages, but the literature attributes the bulk of the decline to schooling.

5. **Border-county Dube-Lester-Reich estimates show null effects even for the highest bite ratios.** The DLR border-pair design holds local labour-market conditions fixed by comparing counties on opposite sides of state borders where one state's bite is much higher. Across the full 1990-2016 panel the estimated elasticity is in [−0.05, +0.05] with confidence intervals tightly around zero. If the spec's border-county informative test confirms this, the primary stratified-DiD finding (if positive) is likely picking up the South/non-South confounder rather than a genuine bite-ratio effect.

**How this steelman should shape the result card:**

The v1 result card must:

(a) Report the cross-cohort differential AND the within-cohort ATTs separately, so readers can see whether the "differential" is driven by an unusually negative HIGH-BITE estimate or an unusually positive LOW-BITE estimate. A negative differential driven by the LOW-BITE cohort showing positive ATTs (the monopsony pattern) is a different finding than a negative differential driven by the HIGH-BITE cohort showing strongly negative ATTs (the Chicago pattern).

(b) Decompose the HIGH-BITE cohort by region (South vs non-South) to address objection #2. If the bite-ratio differential vanishes when regional fixed effects are added, the headline finding is confounded.

(c) Report the border-county DLR informative test as a primary cross-check. If border-pair estimates are tightly null while the cross-cohort differential is large and negative, the spec's primary design is likely capturing state-level confounders the DLR design absorbs.

(d) Add a school-enrolment control (CPS/ACS state-year teen school-enrolment rate) and report the cross-cohort differential with and without it. If the differential attenuates by more than half with school-enrolment control, the framing must qualify the Chicago story.

The strongest version of the steelman argues the bite-ratio framing is a holdover from the pre-2010 literature and that the modern bunching + border-pair evidence has largely settled the question against measurable teen disemployment at the bite ratios actually observed in US history. A finding that the cross-cohort differential exists but is dominated by South/non-South or schooling confounders should be reported as such, not as evidence for the Chicago claim.
