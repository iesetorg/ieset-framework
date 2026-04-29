# Steelman — Austerity output recovery tradeoff

**The strongest argument against this hypothesis:**

The Alesina-Favero-Giavazzi 2019 line of argument is that austerity based on expenditure cuts is less contractionary — sometimes expansionary — than austerity based on tax increases, and that the Blanchard-Leigh multiplier critique does not hold up once the composition of fiscal adjustment is controlled. The European periphery experience 2010-2013 bundled tax-heavy consolidation (which the Alesina camp agrees has high multipliers) with expenditure cuts (which have smaller multipliers in their reading). A spec that treats consolidation as a scalar misses the composition dimension, and may recover a misleadingly large multiplier because the sample is dominated by tax-heavy episodes.

Specific objections the hypothesis must engage with:

1. **Composition of adjustment is the contested parameter.** The Alesina-Favero-Giavazzi research programme reports that OECD consolidations based predominantly on spending cuts produce mild output effects or in some cases expansions (via confidence and expectations channels), while tax-based consolidations produce the large negative multipliers the Blanchard-Leigh paper identified. The Eurozone periphery 2010-2013 was heavily tax-based (VAT increases, income-tax hikes, pension contribution increases). A spec that treats the scalar CAPB change as treatment cannot separate these and may produce a multiplier-estimate that is conditional on the composition mix in this specific sample.

2. **The forecast-error instrument has known problems.** Blanchard-Leigh 2013 instrumented actual consolidation with IMF forecast error. The instrument is plausibly exogenous to underlying economic conditions IF forecast errors reflect only forecasting limitations, not systematically-biased forecasts. Herndon-Ash-Pollin-style scrutiny of the IMF forecasting model shows forecast errors are correlated with starting conditions (countries with severe crises had systematically optimistic forecasts), which breaks the instrument's exclusion restriction. The IV specification may be recovering a weighted combination of the true fiscal multiplier and the forecasting-model error.

3. **Endogenous programme design.** Eurozone periphery countries under Troika programmes did not independently choose their consolidation intensity — it was negotiated with creditor institutions under conditional lending. Programme intensity was calibrated to debt-sustainability constraints and creditor risk-tolerance, not to the country's output-gap dynamics. The "consolidation intensity" variable partly measures creditor stringency, which is not the same as the fiscal-choice variable the hypothesis treats it as. The instrument does not address this because the forecast errors are computed against the post-programme-design forecasts.

4. **Ireland's recovery is a counter-example the hypothesis downweights.** Ireland consolidated aggressively 2010-2013 and recovered growth by 2014, faster than the spec's prediction would suggest. The recovery was driven partly by multinational-tax-base volume (which distorts GDP measurement, see Irish GDP revisions post-2015) but also by genuine tradeable-sector recovery. Treating Ireland as part of the periphery-consolidation sample may anchor the hypothesis in ways that don't generalise to cases where consolidation occurred without Ireland's tradeable-sector dynamism.

5. **The 2010-2019 window truncates the recovery.** Periphery economies continued to close output gaps 2019-2023 (interrupted by COVID) and had recovered further by pre-COVID levels. Extending the window into the recovery phase would reduce the measured cumulative-output loss and the implied multiplier. The pre-registered 2010-2019 window captures the slow recovery but may systematically understate eventual convergence. The falsification rule addresses this only indirectly by including cumulative output as one of the outcomes.

**How this steelman should shape the result card:**

The v1 result card must:

(a) Decompose the CAPB change into revenue-side and expenditure-side components and report separate coefficients. If the tax-heavy component carries the negative output effect and the spending-cut component is weaker or neutral, the headline multiplier needs composition-qualifier language.

(b) Report the 2SLS first-stage F-statistic and a Kleibergen-Paap weak-instrument test. If the instrument is weak, the finding is fragile and must be flagged.

(c) Present Ireland as a special case (with standard-GDP vs modified-gross-national-income outcomes) so readers can see whether the case is driving or moderating the average effect.

(d) Extend the output-recovery outcome window to 2022 (pre-COVID peak) as a v2 companion and report whether cumulative output loss attenuates materially. If it does, the headline "slow recovery" framing is time-truncated and must be qualified.

The strongest version of the steelman argues the hypothesis conflates "austerity" with "tax-based austerity in a monetary-union periphery with crisis-level sovereign spreads." Those conditions may be necessary for the large-multiplier finding, and the generalisation to "austerity is harmful" is too broad. A v2 with composition decomposition is probably the right next step and would plausibly show the relationship is conditional on both composition and monetary-policy space.
