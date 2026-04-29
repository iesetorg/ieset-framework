# Steelman — ESOP firm survival and productivity post-1974 ERISA

**The strongest argument against this hypothesis:**

The published ESOP-vs-non-ESOP "higher survival, comparable productivity" finding is principally a selection artefact of which firms become ESOPs in the first place, and a measurement artefact of how the ESOP literature constructs its "matched" control samples. The flagship results (Blasi-Kruse-Freeman, the NCEO panels, Kruse-Blasi-Park) are not from a randomised treatment of ownership; they are from owner-founders deciding to sell to an ESOP at moments when (a) the firm is profitable enough to support the leveraged buyout, (b) succession planning is already a pressing concern, and (c) the §1042 tax deferral is materially valuable. Each of those is a positive selector on subsequent survival. The conventional matched non-ESOP control firm has none of those filters running on it.

Specific objections the hypothesis must engage with:

1. **Selection on profitability and succession-readiness.** ERISA-1974 made ESOPs a tax-advantaged exit vehicle, but the §1042 deferral (Deficit Reduction Act 1984) only matters when the seller has a large embedded gain — i.e. when the firm has been profitable for a long time. ESOPs are therefore a post-success population, not a random draw from the firm distribution. Any survival-rate gap that does not control for pre-ESOP profitability trajectory is contaminated.

2. **Industry composition.** ESOPs cluster in mature, asset-light, professional-services and skilled-manufacturing sectors where founders have something worth selling and continuity matters. They are scarce in fast-cycle tech, commodity extraction, and pure-arbitrage finance. Industry-and-size matching narrows the gap but does not close it: within an industry, ESOP candidates are a self-selected slice of the more stable founder-owned firms.

3. **Survivorship bias in the panels themselves.** The NCEO database tracks ESOPs as they form and re-survey them; firms that fail are dropped from later waves. The Blasi-Kruse-Freeman 2003 sample is built from a list of 1980s-1990s ESOPs that were still surveyable in the late 1990s — a non-trivial source of right-censoring on failures. The matched non-ESOP control set is typically drawn from Compustat or D&B with full population coverage, so apparent survival differences partly reflect different sampling frames.

4. **The productivity finding is "no worse, possibly better" — a weak claim.** The strongest defensible version of the literature is "ESOP adoption does not destroy productivity, and may modestly raise it where coupled with high-involvement HR practices." That is a much weaker claim than the popular framing of ESOPs as a productivity-enhancing ownership form. The hypothesis's "comparable productivity" framing is at least defensible; "higher productivity" would not be.

5. **Macro placeholder is non-informative.** US GDP per person employed (the WDI macro series this v2 has on disk) cannot identify any ESOP effect: ESOPs are at most ~10-15% of US private-sector employment, and the dominant variation in macro labour productivity is driven by ICT capital deepening, sectoral shift, and the post-2005 productivity slowdown — none of which have anything to do with ownership form. Treating the macro series as informative for the ESOP question is a category error.

**How this steelman should shape the result card:**

Until firm-level NCEO and Blasi-Kruse-Freeman matched panels (or a Census-LBD ESOP linkage) land on disk, the v2 result card must:

(a) Label the run honestly as `inconclusive — data gap`, not as a tentative `partial` or `weakened` based on macro proxies.

(b) State explicitly which fetcher would close the gap: NCEO ESOP database (firm-year panel of ESOP formations and survival), and a Compustat or D&B matched non-ESOP control draw. The Census Longitudinal Business Database with Form 5500 ESOP linkage would be the gold standard.

(c) Report the macro series only as a context line in the chart, never as the verdict-determining statistic. The v2 spec gates the verdict on a METHOD_VALID firm-level panel; the macro series is INFORMATIVE-only and cannot move the verdict by itself.

(d) Note that even when the firm-level panel arrives, the strongest version of this hypothesis can only be tested by exploiting plausibly exogenous variation in ESOP adoption — e.g. the §1042 introduction in 1984 as a difference-in-differences shock to founder incentives, or state-level ESOP-promoting tax provisions. A simple matched-sample comparison will remain identification-weak even with the best data.
