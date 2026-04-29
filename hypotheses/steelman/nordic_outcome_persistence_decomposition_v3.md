# Steelman — Nordic outcome persistence decomposition v3

**The strongest argument against the framework's within-country DiD design:**

v3 hands-picks four treatment events from a sample of 10 countries, assigns intuitive signs, and tests whether post-treatment trajectories confirm the narrative. That's not identification; that's narrative-driven specification choice. On this n and this sample, almost any cleanly-timed reform will look like it "worked" because the comparison countries are France, Denmark, Finland, and Iceland — all of which had substantial institutional quality and reasonable 1996-2023 outcomes to begin with. The absence of a credible counterfactual (what would Italy have looked like if it had reformed in 1999?) means β_stagnation identifies "Italy vs the average of other countries over 1999-2023" — a number that will almost certainly be negative for reasons unrelated to the reform claim.

Specific objections:

1. **Treatment date selection is non-blinded.** NOR 2001, SWE 1999, ITA 1999, GRC 2001 were picked because the author knows in advance which ones ended well and which badly. Even with pre-registered commitments, the selection set is small enough that the "which countries / which dates to code" step has already absorbed most of the identification degrees of freedom.

2. **Staggered TWFE with heterogeneous effects is biased** (Goodman-Bacon 2021, Callaway-Sant'Anna 2021, de Chaisemartin-d'Haultfœuille 2020). With four treated countries on two different dates plus six controls, the TWFE coefficient is a weighted average of treatment-effect-by-cohort terms with unknown weights. The sign of β could flip if the heterogeneity is real. A robustness spec using the Callaway-Sant'Anna estimator is required, not optional.

3. **Parallel trends is untestable with n=4 treated countries.** The pre-trend placebo has too little power to credibly rule out violations. A spurious-effect placebo that does not detect an effect is consistent with null-power, not with parallel trends holding.

4. **The 2008 GFC and 2020 COVID are global shocks that hit post-euro-entry SE countries differently from Nordic countries.** Any within-country trajectory comparison over 1996-2023 absorbs these shocks into year FE, which is supposed to handle common shocks. But the shock WAS heterogeneous — SE countries were more exposed. Year FE may over-correct, masking the causal effect of the treatment OR masking the absence of one.

5. **Italy's poor performance in the period is confounded by demographic decline.** Italian working-age population shrunk; log-per-capita GDP measures take that as a headwind. β_stagnation will be negative partly for demographic reasons independent of the euro-entry-without-reform coding.

6. **Greek post-2010 austerity is in the sample.** The Greek trajectory 2010-2018 is dominated by Troika-imposed austerity, not by the pre-2010 fiscal-dominance dynamics. Yet the pre-reg codes GRC as fiscal-dominance-treated from 2001 onward through 2023. The resulting coefficient muddles two distinct movements into one indicator.

7. **Even a clean positive β_reform doesn't establish causation for the policy-content claim.** Norway's 2001 rule worked BECAUSE Norway already had high institutional quality in 2000. A country with lower baseline institutions adopting the same rule would likely fail to sustain it. The framework's D.2.9 condition entry already acknowledges this; v3's identification cannot separate "the rule caused the outcome" from "the Nordic institutional substrate made both the rule and the outcome possible."

**How this should shape the v3 result card:**

- If β_reform > 0 and β_stagnation < 0 with clean pre-trends: report honestly but caveat that the finding is consistent with treatment-effect interpretation AND with substrate-interpretation. Distinguishing requires cases where similar rules failed in low-substrate countries — a comparative-institutional analysis outside the current sample.
- Run Callaway-Sant'Anna robustness in v3.1 regardless of v3.0 verdict; if signs flip, v3.0's conclusion is suspect.
- Split Greece into two movements (fiscal-dominance 2001-2010, austerity 2010-2018) in v3.2.
- Decompose Italian trajectory by age-adjusted productivity per hour to address demographic confound.
- Treat v3.0 as the first pass through this design, not as the final word.
