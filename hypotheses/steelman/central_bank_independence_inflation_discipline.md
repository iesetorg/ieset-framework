# Steelman — Central bank independence and inflation discipline

**The strongest argument against this hypothesis:**

The cross-country correlation between CBI indices and inflation is a selection artefact, not a causal regularity. Countries that granted independence to their central banks in the 1990s did so as part of a broader disinflationary turn that included fiscal reform, trade liberalisation, and anti-inflationary political commitments. The CBI statute codifies the disinflationary consensus; it does not produce it. Reversing the statute in the absence of the underlying consensus would not return inflation; preserving the statute without the consensus would not prevent it.

Specific objections the hypothesis must engage with:

1. **Endogenous adoption.** Governments adopt CBI when they have lost credibility and are trying to import it; they retain it when the political economy of low inflation has already won. Cross-country variation in CBI therefore tracks where countries are on the disinflation cycle, not the causal effect of the statute. A spec that uses within-country variation mitigates this but does not solve it — the reforms themselves are timed to moments when discipline has arrived.

2. **The de-jure / de-facto gap is the entire ballgame.** Garriga's index captures statutory provisions; de-facto independence is what determines outcomes. Venezuela, Argentina, Turkey, and Zimbabwe have all had formally independent central banks during periods of severe inflation; reconciling this requires either a de-facto measure (CEO turnover, Cukierman 1992) or an honest acknowledgement that the de-jure correlation is partly mechanical (legal independence correlates with legal infrastructure generally). The hypothesis engages this via WGI GE as a secondary variable, but WGI GE is itself partly an outcome variable.

3. **The post-1990 sample is the easy regime.** The 1970s-1980s provided the variation the literature was built on: high-CBI Germany / Switzerland contrasted with low-CBI Italy / UK. Post-1990, nearly all advanced economies converged to high CBI and low inflation, and the cross-sectional variation collapsed. Emerging-market variation remains, but there the coefficient is identified off countries with weak institutions generally, not off CBI specifically. Running on 1990-2023 may produce a weaker result than the pre-1990 literature suggests — not because the mechanism failed but because the sample lost its discriminating variation.

4. **The 2021-2023 inflation shock is a stress test the hypothesis may fail.** Fully-independent Fed, ECB, and BoE all experienced the largest inflation shocks in 40 years simultaneously. If statutory independence delivers low inflation, the cross-country pattern of 2021-2023 inflation outcomes should track remaining CBI variation — but it tracked exposure to energy import shocks and supply-chain disruption far more than any CBI variable. The hypothesis's falsification rule evaluates the full 1990-2023 panel; whether the post-2021 shock drags the coefficient toward zero is a meaningful empirical question, not a nuisance.

5. **Inflation targeting vs independence conflation.** Many of the institutional reforms that happened in the 1990s bundled CBI with inflation targeting, transparency requirements, and fiscal-monetary separation laws. The CBI index captures one dimension of this bundle. The inflation-reducing effect attributed to CBI may actually belong to IT or to the joint package; disentangling requires a separate regressor for IT regime adoption, which the v1 spec does not include.

**How this steelman should shape the result card:**

The v1 result card must:

(a) Report the de-jure (Garriga) coefficient alongside a de-facto proxy (Cukierman CEO turnover rate, or a constructed index from governor replacement dates) so readers see whether the statutory measure is doing the work or whether only the de-facto component carries explanatory weight.

(b) Split the panel into pre-2008 and post-2008 subsamples and report both coefficients. A regime-dependent finding would substantially qualify the causal reading.

(c) Add an inflation-targeting regime indicator (from Rose 2007 or Hammond 2012) as an alternative treatment variable and compare the coefficient magnitudes. If IT does the work and CBI coefficient collapses, the hypothesis is really about IT, and the framework should update accordingly.

(d) Note explicitly that the cross-country correlation is compatible with the selection story (the disinflationary consensus drives both statute and outcome) and that the panel's within-country identification is the stronger reading.

The strongest version of the steelman points at a V-Dem / historical robustness exercise: code major CBI reforms (Germany 1957, USA 1978 Humphrey-Hawkins, NZ 1989, Eurozone 1999, UK 1997) as event studies and test whether inflation falls measurably in the 5-year window after the reform once pre-existing trends are controlled. That's a different identification strategy and belongs to a v2.
