# Steelman — Fiscal multipliers higher at the ZLB than in normal regimes

**The strongest argument against this hypothesis:**

The "ZLB multipliers are substantially higher" claim leans heavily on
two US identifications (Ramey-Zubairy 2018 with defence-news shocks;
Auerbach-Gorodnichenko 2012 with regime-switching VARs) whose
international generalisability is much weaker than the headline result
suggests. A spec that codes the New-Keynesian theoretical prediction
as if it had clean cross-country empirical backing risks reading too
much into a finding that is fragile outside the US sample, sensitive
to the choice of regime indicator, and confounded with the Great
Recession itself.

Specific objections the hypothesis must engage with:

1. **The Ramey-Zubairy 2018 result is itself qualified.** Their own
   paper concludes that the evidence for higher multipliers under
   slack/ZLB is weaker than the Auerbach-Gorodnichenko 2012 finding —
   the cumulative ZLB multiplier they estimate is in the 0.4-0.8
   range, not the 1.5-2.0 range that animates the "substantial"
   framing. Setting the spec's PRIMARY threshold at gap >= +0.5 is
   already at the upper end of what the most-cited identifications
   actually deliver; pushing it higher would be unfair to the
   New-Keynesian school, but readers should understand that the
   threshold is calibrated to the empirically thin claim, not the
   textbook theoretical claim.

2. **Cross-country identification is even thinner.** The
   Owyang-Ramey-Zubairy 2013 international panel covers only Canada,
   the UK, and the US for the news-shock series; there is no
   comparable narrative shock series for Germany, France, Italy, Japan
   or the smaller European economies that this spec's 21-country panel
   needs. Promoting US-style results to the OECD panel implicitly
   relies on identification that does not exist in the literature.

3. **The ZLB regime indicator is endogenous to the shock.** Countries
   are at the ZLB precisely when aggregate demand is weak, and weak
   demand is itself a determinant of the multiplier (slack-state
   non-linearity). State-dependent LP-IV cannot fully separate the
   "ZLB" channel (no monetary offset) from the "slack" channel
   (Keynesian crowding-in via employment of idle resources). The
   New-Keynesian story attributes the larger multiplier to suppressed
   crowding-out via the policy rate; the slack story attributes it to
   the supply curve being flat. The two are observationally
   indistinguishable in the data the spec uses.

4. **The 2008-2021 ZLB window is dominated by one event.** Most ZLB
   country-quarters in the OECD panel come from 2009-2015 (post-GFC)
   and 2020-2021 (COVID). The estimated ZLB multiplier is therefore
   primarily identified off the GFC recovery and COVID stimulus —
   episodes with idiosyncratic features (financial-system repair,
   household stimulus checks, supply-chain disruption) that the
   "normal-regime" comparison sample does not share. The spec's
   exclusion of COVID 2020Q2 mitigates but does not remove this
   confound.

5. **Publication bias and specification search.** The fiscal-
   multiplier literature has visible specification search around the
   slack/ZLB result; meta-analyses (Capek and Crespo Cuaresma 2020;
   Gechert and Rannenberg 2018) report substantial dispersion across
   reasonable identification choices, and the headline "above 1 at the
   ZLB" claim is sensitive to whether one uses news shocks vs SVAR
   ordering vs Blanchard-Perotti. A pre-registered LP-IV is a real
   step forward, but readers should treat any single estimate as one
   draw from a wide distribution.

6. **The US-only diagnostic in v1 points the wrong way.** The first
   run's downgraded US-only OLS LP on FRED quarterly data 1995-2021
   (FGEXPND deflated by GDPDEF, ZLB indicated by FEDFUNDS <= 0.25%)
   produces a NEGATIVE gap at h=8: ZLB multiplier is roughly zero or
   slightly negative while the normal-regime multiplier is around 0.5,
   for a gap of about -0.6 — directionally OPPOSITE the New-Keynesian
   prediction. This is not adjudicating evidence (the spec demands
   panel LP-IV with narrative IV; this is a non-IV US-only OLS LP) but
   it does flag that even the most-favourable single-country
   identification on disk does not obviously support the claim.

**How this steelman should shape the result card:**

The v1 result card already handles (1) and (2) by emitting
`inconclusive (data gap on ...)` rather than declaring SUPPORTED on
the basis of the favourable US literature. A v2 must:

(a) Once OECD quarterly NAQ_GDP and a `manual:ramey_defence_news`
publisher are on disk, run the full state-dependent LP-IV on at least
the Owyang-Ramey-Zubairy 3-country panel (USA, GBR, CAN) before
attempting the full 21-country panel. If the 3-country panel does not
clear the +0.5 gap threshold, attempting the 21-country panel by
substituting forecast-error shocks for the missing narrative IVs would
be a weak-instrument problem that the verdict must own.

(b) Report the "slack" specification (output-gap < some threshold) as
a robustness alternative to the "ZLB" specification. If the slack
indicator does the same explanatory work, the New-Keynesian
crowding-out channel is not identified separately from the
supply-curve-flat channel and the verdict should be downgraded to
`partial` regardless of the headline gap.

(c) Document the heterogeneity: report country-by-country regime gaps,
not just the panel mean. If the gap is +1.5 in the US and -0.5 in
Germany and Japan, the panel mean of +0.3 is not adjudicating the
claim — it is averaging over economies where the channel works and
economies where it does not. The New-Keynesian school's defence is
that the channel is universal; refuting that defence requires the
gap to be positive in most of the panel, not just on average.
