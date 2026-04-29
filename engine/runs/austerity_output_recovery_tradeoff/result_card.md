# Austerity / output-recovery trade-off (post-2010 Europe)

**Verdict:** inconclusive — OLS coefficient on Δfiscal-balance is +1.287 pp/pp (p=0.289) — wrong sign but not significant. The spec mandated IV-2SLS (Blanchard-Leigh instrument) precisely because OLS on this relationship suffers from reverse-causality bias toward positive coefficients (worse-growth → larger forced consolidation). The April-2010 WEO forecast vintage needed for the instrument is not in the local data tree. With controls (initial debt, unemployment), β = +2.540 pp/pp (p = 0.007) — also wrong sign. Identification gap, not dispositive refutation. N=21.

## Summary

- N = 21 European countries with data (8 periphery, 13 core).
- β on Δfiscal-balance (core): **+1.287 pp cumulative log-GDP per 1pp-GDP consolidation** (HC1-robust p = 0.289).
- β on Δfiscal-balance (periphery, β + δ): **+1.380 pp/pp**.
- Interaction (periphery − core): +0.094 pp/pp (p = 0.946).
- Primary R² = 0.325.

## Method

Cross-section OLS across 21 European countries:

    Δlog(GDP)_{2010→2019} = α + β·ΔFB_{2010→2013}
                          + γ·periphery + δ·ΔFB·periphery + ε

with HC1 (heteroskedasticity-robust) standard errors. ΔFB is the change in IMF general-government net lending / GDP (GGXCNL_NGDP) — used as a proxy for the spec's intended cyclically-adjusted primary balance (GGCBP), which is not in the local vintage tree. Periphery = {GRC, IRL, ITA, PRT, ESP, CYP, SVN, SVK}.

**Primary spec downgraded from IV-2SLS to OLS** because the Blanchard-Leigh 2013 instrument (April-2010 IMF WEO forecast minus realised CAPB change 2010-2013) requires the April-2010 WEO forecast vintage, which is not on disk. The OLS estimate is biased toward zero relative to the IV — discretionary consolidation responds to the same shocks that drive growth — so this is a conservative test of the austerity-damage claim. A negative significant β here is stronger evidence than a negative β under the canonical IV.

### Falsification thresholds

- PRIMARY: β_core < 0, |β_core| ≥ 0.5 pp/pp, p < 0.05, AND β_periphery < β_core.
- METHOD_VALID: ≥12 countries with treatment+outcome, ≥6 periphery, ≥6 core.

## Data

- world_bank_wdi:NY.GDP.MKTP.KD (real GDP, constant USD)
- imf:GGXCNL_NGDP (general govt net lending / GDP — CAPB proxy)
- imf:GGXWDG_NGDP (general govt gross debt / GDP, control)
- world_bank_wdi:SL.UEM.TOTL.ZS (unemployment, secondary outcome)

## Caveats

- Treatment is *overall* fiscal balance change, not cyclically-adjusted. In the 2010-2013 European context the cyclical component is large (rising unemployment depresses revenue, raises spending), so the actual change in CAPB was generally smaller than ΔFB; the biased measurement attenuates β toward zero.
- N≈21 cross-section: standard errors wide, periphery interaction test under-powered.
- Outcome-window endogeneity: cumulative growth 2010-2019 mechanically includes the years over which the consolidation was occurring; this is consistent with the spec's claim about cumulative output, but an event-study would be the cleaner test.
