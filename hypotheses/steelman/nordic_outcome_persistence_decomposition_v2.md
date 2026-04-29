# Steelman — Nordic outcome persistence decomposition v2

**The strongest argument against the framework's v2 expanded-channel approach:**

v2 is channel-throwing. The v1 finding was that three variables didn't explain the Nordic-vs-Southern-Europe gap. v2 adds five more and hopes the residual shrinks. Even if it does, the interpretation problem hasn't gone away — all the channels are cross-sectional institutional-quality indices, most of them built partly from measurements of the outcomes they're being used to explain. Expanding an endogenous channel set doesn't fix the endogeneity; it just spreads it over more predictors.

Specific objections the v2 result must engage with:

1. **Multicollinearity at n=278.** Eight channels on a panel of 10 countries × 28 years with a lot of missingness means channels are highly colinear and the individual coefficients are unstable. The residual share may change not because more channels explained the gap but because the near-singular design matrix is soaking up variance in unstable ways. v2 must report channel VIFs and sensitivity of the residual share to dropping one channel at a time.

2. **WGI endogeneity doubles up.** Adding Control of Corruption and Regulatory Quality to the existing Government Effectiveness and Rule of Law gives us *four* WGI indicators, all built from the same underlying surveys and expert panels, all partly downstream of outcomes. If they all move together and all correlate with the outcome, the residual shrinks for purely mechanical reasons, not because we've identified an institutional channel that causes the outcome.

3. **Fiscal-surplus flow as channel is ambiguous.** Net lending/GDP being higher in Nordic countries than Southern Europe is TRUE, but it's partly an outcome of the income level (richer countries tax more efficiently and spend more prudently), partly a consequence of Norwegian oil revenues, and partly a feature of small-open-economy trade surplus dynamics. Treating it as an explanator of GDP/capita imports all three confounds.

4. **Current account as channel has the same reverse-causation problem.** Nordic current-account surpluses are a consequence of competitive export sectors and high savings rates, which are themselves consequences of the Nordic institutional arrangement being studied. Current-account/GDP is partly an outcome in disguise.

5. **Trade openness captures a national size and geography artefact.** Nordic economies are small; they trade more as a % of GDP almost by definition. Spain, Italy, France are larger and have bigger internal markets. The trade-openness gap may be a scale effect, not a policy-posture effect.

6. **If v2's residual does shrink below 0.30, the conclusion is weaker than it looks.** "Eight institutional-quality indices explain the Nordic GDP gap" is almost tautological — the indices were built to summarise institutional quality, and Nordic countries score high on institutional quality by construction. The test the user would actually find persuasive is whether Nordic-specific *reforms* (Bildt, Nyrup, Norwegian SWF, Schröder Agenda) predicted within-country outcome improvements — a trajectory and movement-level claim v2 still does not test.

**How this steelman should shape the v2 result card:**

If v2 residual share drops below 0.30 on the primary outcome:
- Report channel VIFs + leave-one-out sensitivity on each channel's contribution.
- Explicitly flag the endogeneity concern for the four WGI indicators and propose V-Dem administrative indicators as a v2.1 robustness.
- Caveat that the finding is consistent with "channels capture the outcome more fully" and does NOT establish that the channels cause the outcome.
- Transition clearly: v2 supports the decomposition-as-explanation framing but does not test the timing-of-reforms critique; v3 remains the right test for that.

If v2 residual share stays above 0.30:
- Report the null honestly.
- Update the framework's position: cross-sectional decomposition on this sample is exhausted; the Nordic question requires within-country trajectory analysis with movement-level treatment effects. v2 refutes the "just add more channels" framing decisively.

Either outcome moves the research agenda forward; a muddled middle result is the one to be most wary of.
