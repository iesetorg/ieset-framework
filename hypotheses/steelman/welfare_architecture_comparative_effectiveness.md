# Steelman — Welfare architecture comparative effectiveness

**The strongest argument against this hypothesis:**

The forced-saving vs universal-transfer distinction is a useful heuristic that decomposes poorly under scrutiny. Every real welfare state is a hybrid, and the "architectural category" assigned by the spec is partly the analyst's judgement call. Singapore's CPF is forced saving but is heavily subsidised and tax-advantaged by government; Australia's superannuation is mandatory but combined with a means-tested age pension that catches non-savers; Chile's AFP has been repeatedly retrofitted with minimum pensions, solidarity pillars, and state matches. The Nordic universal-transfer systems have in practice evolved meaningful tax-advantaged private-pension pillars (Sweden's premium pension) that are structurally similar to forced saving. The architecture categories the hypothesis compares are adjectives attached to convergent regimes, not cleanly different treatments.

Specific objections the hypothesis must engage with:

1. **Survivor bias in the forced-saving cases.** Singapore, Chile, and Australia are three of the most-cited forced-saving cases, and their apparent success reflects specific national conditions (Singapore's financial-sector depth, Chile's commodity revenues, Australia's compulsory-superannuation political stability) that were not guaranteed at reform-time. Many countries attempted forced-saving reforms with poor outcomes (Argentina 1994, Hungary 1998, several Central European countries post-2008) or had to roll them back. Restricting the forced-saving category to the three successful cases builds the answer into the sample. A fuller sample should include the failed and reversed cases, which would push the adequacy and sustainability estimates in less favourable directions.

2. **The replacement rate is the wrong adequacy metric.** OECD's replacement rate measures the retiree's first-year-of-retirement income relative to their final earnings. It does not measure adequacy across the whole retirement span, nor does it measure dispersion across the retired population. Forced-saving systems deliver high replacement rates for the median worker with a stable career; they deliver very poor rates for workers with interrupted careers, informal-sector employment, or early death-of-spouse. Universal-transfer systems have flatter but floor-protecting profiles. Comparing median replacement rates flatters the forced-saving cases and hides the distributional cost.

3. **Sovereign liability comparison is an apples-to-oranges exercise.** The hypothesis treats forced-saving implicit liabilities as near-zero and universal-transfer liabilities as large. But this accounting convention is arbitrary: the forced-saving government still bears the residual liability when markets crash, when the saver under-accumulates, and when the minimum-pension backstop kicks in. Chile's AFP collapse in 2008-2011 and again in 2020 with early-withdrawal legislation shifted liability back onto the state. A proper liability measure would include the implicit option-value of the residual state backstop; the v1 spec does not attempt this.

4. **Political economy asymmetry.** Universal-transfer systems face political pressure to expand benefits; forced-saving systems face political pressure to allow early withdrawals (COVID-era Peru, Chile, Australia all permitted super withdrawals, undermining the forced-saving premise). Both architectures are subject to political drift, but the drift directions differ. A cross-sectional snapshot will see universal-transfer systems at their most-expanded point and forced-saving systems at or near their design specification — favouring the latter in fiscal comparison. A multi-period comparison that lets political drift run its course would produce different relative rankings.

5. **The NHS is not the welfare architecture the hypothesis is testing.** Treating the UK NHS as exemplar of universal-transfer architecture conflates the pensions architecture (UK has a relatively small state pension and a large private-pension pillar, making UK quite forced-saving-adjacent) with the healthcare architecture (NHS, which is universal but unrelated to pension adequacy). The spec's pension outcomes are not meaningfully comparable against an NHS-based coding. Splitting architectures by outcome domain (pensions vs healthcare vs income support) would be more honest but requires three separate hypotheses.

**How this steelman should shape the result card:**

The v1 result card must:

(a) Report adequacy outcomes conditional on career type (stable-wage-earner, interrupted-career, low-wage-career). If forced-saving systems do well only for the stable-career quantile, the headline "comparable median adequacy" is misleading.

(b) Report sovereign liability including a "contingent backstop" estimate that reflects the option value of state intervention when forced-saving returns disappoint. If this materially changes the fiscal-liability ranking, the finding is qualified.

(c) Include the failed/reversed forced-saving cases (Argentina, Hungary, Poland, Peru early-withdrawal waves) in the robustness specification and report whether the architectural advantage persists once survivor bias is addressed.

(d) Separate pension-architecture from healthcare-architecture from income-support-architecture. The conflation in the v1 coding is a known weakness and must be visible to readers.

The strongest version of the steelman argues the hypothesis is under-specified: "architecture" is a composite that the empirical test cannot cleanly decompose, and the data will support whatever pattern the coder's architectural judgement calls predict. A v2 should either pick a single outcome (pension replacement) and a single treatment dimension (mandatory-saving-share-of-retirement-income) or reframe the hypothesis around specific institutional features rather than architectural labels.
