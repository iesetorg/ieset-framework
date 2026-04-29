# Steelman — Labour market flexibility and unemployment duration

**The strongest argument against this hypothesis:**

The EPL-duration relationship was a confident finding of the 1990s labour-economics literature (Nickell 1997, Blanchard-Wolfers 2000) that has been substantially qualified by the 2010s revisionist literature. Bassanini-Duval 2006, Howell 2005, and a series of OECD Employment Outlook chapters have argued that the EPL-unemployment-outcome relationship is weaker, more conditional, and more fragile than the early consensus suggested. The hypothesis reproduces a 1990s finding that the field has since moved past, and risks projecting confidence where the literature has grown more humble.

Specific objections the hypothesis must engage with:

1. **The OECD EPL index is a measurement artefact.** OECD EPL v1 and v2 differ substantially in methodology; even within a version, the index aggregates procedural requirements, notice periods, severance pay, and judicial-review probability into a single scalar. Countries with similar scores have very different real-world firing-cost structures (Germany's Works Council requirement vs Italy's judicial-review requirement are both "high" in the index but generate very different firm behaviour). Using EPL as a scalar regressor treats very different regulatory regimes as interchangeable, biasing the estimate toward zero if the different components have offsetting effects.

2. **Endogeneity of EPL reform timing.** Countries reform EPL when labour-market performance is poor (Germany 2003 Hartz reforms, Spain 2012 post-crisis, Italy 2014 Jobs Act). The pre-reform high-duration period reflects the conditions that motivated the reform, and the post-reform period reflects recovery from those conditions. The within-country identification picks up the cyclical component as much as the policy component. A spec that uses the forecast-error or surprise-reform approach would be cleaner.

3. **Nordic counter-examples.** Denmark and Sweden combine relatively strict EPL (by OECD measure) with low unemployment duration and high transition rates. The Danish flexicurity model is the canonical counter-case: EPL is moderate-high, benefit generosity is high, ALMP spending is high, and duration outcomes are good. The hypothesis's control set includes UI replacement rate and ALMP spending but the interaction effects are not explicitly modelled. A linear specification that enters EPL, UI, and ALMP as additive controls misses the complementarity relationship that the flexicurity framework emphasises, and will estimate an EPL coefficient that does not represent the underlying regime logic.

4. **Insider-outsider effects and heterogeneity.** The EPL effect may be concentrated on specific worker groups (youth, migrants, less-educated) and absent or reversed for prime-age skilled workers. Aggregate duration measures average across these groups and hide the distributional effect. If the hypothesis's falsification rule is met in the aggregate, the framework would report "EPL lengthens duration" when the truthful statement is "EPL lengthens duration for some worker groups and has opposite or null effects for others." The v1 spec does not disaggregate.

5. **The matching-function microfoundation assumes homogeneous labour.** Mortensen-Pissarides in its textbook form treats workers and jobs as homogeneous. Real labour markets have skill mismatch, spatial mismatch, and sectoral reallocation dynamics that EPL affects differently. A well-functioning labour market with high EPL may have long durations not because of friction but because of deliberate search for better matches (Nordic case); a poorly-functioning market with low EPL may have short durations because workers accept bad matches quickly. Duration is not a clean welfare metric, and the hypothesis treats it as one.

**How this steelman should shape the result card:**

The v1 result card must:

(a) Disaggregate EPL into its subcomponents (procedural requirements, notice periods, severance pay, judicial-review probability, collective-dismissals rules) and report separate coefficients. If the scalar index is concealing offsetting subcomponent effects, the headline is misleading.

(b) Report the EPL effect by worker-group subsample (youth, prime-age, older) where OECD data permits. If the effect is concentrated on youth unemployment duration and absent for prime-age workers, the policy implications shift substantially.

(c) Include an EPL × UI interaction term and an EPL × ALMP interaction term. If the EPL coefficient is positive in low-UI, low-ALMP regimes and zero or negative in the flexicurity regime, the additive specification is misrepresenting the data-generating process.

(d) Report both the aggregate-duration outcome and the transition-rate outcome. If EPL lengthens duration but also raises match quality (proxied by subsequent job tenure or wage gains), the welfare interpretation is ambiguous.

The strongest version of the steelman argues the hypothesis should be re-cast as: "EPL affects the duration-turnover trade-off, with outcome-quality effects that depend on institutional complements." That claim is more defensible and more interesting; the v1 single-coefficient estimate is a partial summary of a more nuanced relationship. A v2 with interaction terms and subcomponent disaggregation is probably the right follow-up.
