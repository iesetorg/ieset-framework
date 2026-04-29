# Steelman — Trade liberalisation growth effect

**The strongest argument against this hypothesis:**

Trade-liberalisation events are not isolated treatments. They are bundled with stabilisation packages, institutional reforms, exchange-rate realignments, capital-account opening, and political transitions. Attributing subsequent growth to the tariff schedule alone is a classic "treatment bundle" identification failure. The Rodriguez-Rodrik 2001 critique of Sachs-Warner established that the liberalisation-growth relationship in cross-country panels is fragile to dropping a handful of countries, to alternative liberalisation codings, and to the inclusion of bundled reform variables. The hypothesis as specified does not cleanly escape that critique.

Specific objections the hypothesis must engage with:

1. **The liberalisation bundle is the real treatment.** China's WTO accession coincided with two decades of gradually-built market institutions, SOE reform, and a demographic dividend. Attributing China's post-2001 growth to tariff reductions alone is implausible; tariffs were not the marginal constraint. India 1991 bundled trade liberalisation with industrial-licensing removal, exchange-rate realignment, and capital-account partial opening. The v1 spec adds institutional-quality controls, but the controls are coarse and backward-looking. A cleaner test would require identifying a country where trade liberalisation happened without bundled reform — and such cases are rare because liberalisation is politically costly and typically occurs only alongside broader reform packages.

2. **Reverse causation on openness.** Countries that grow fast become more open: their export industries develop, their imports expand, and the trade-to-GDP ratio rises mechanically. Using trade-openness change as the treatment proxy would pick up growth-to-openness causality as much as openness-to-growth. The spec mitigates this with event-based Wacziarg-Welch coding, but the event dates themselves are judgement calls — and the judgement is partly conditioned on subsequent growth outcomes in the literature the dates come from.

3. **Synthetic controls on CHN, IND, NZL, VNM are weak identification.** China's post-2001 growth is sui generis — the synthetic comparator will be a weighted combination of countries that look nothing like China on any relevant dimension. The synthetic control will fit pre-treatment but mean very little post-treatment. Similar problems for Vietnam. New Zealand 1984-1991 is a developed-country case in a small sample of developed-country liberalisers; the synthetic will be drawn from a narrow donor pool. This is a general weakness of synthetic-control methods on "outlier" treatment units.

4. **The 10-year horizon hides the J-curve.** Every major liberalisation episode produces short-run dislocations: import-competing industry contraction, unemployment, real-wage adjustment. NZ 1984-1991 was followed by 5-7 years of very poor performance before the "Rogernomics" growth pattern took hold. India post-1991 had its first 2-3 years of disappointing growth. Picking the 10-year horizon front-loads the recovery phase; picking a 5-year horizon might reverse the sign. The spec pre-registers 10 years, which is defensible, but the framework must acknowledge that the sign of the effect depends materially on the horizon chosen.

5. **Counter-examples exist and matter.** Sub-Saharan African countries that opened in the 1980s under IMF structural adjustment (GHA, KEN, ZMB) did not experience the expected growth surge; Latin America in the 1990s had mixed results; the 1994-1998 financial-crisis Asian economies opened further and suffered severe downturns. These are in the sample but the canonical-case pre-registration foregrounds the successful cases. A symmetric pre-registration would list the weak cases too and ask whether they support or falsify.

**How this steelman should shape the result card:**

The v1 result card must:

(a) Report the 5-year, 10-year, and 15-year ATT side by side, noting the J-curve issue. If the sign changes across horizons the finding is horizon-dependent and must be presented as such.

(b) Present the Callaway-Sant'Anna staggered DiD with and without institutional-quality controls. If the effect attenuates > 60% with institutional controls, the pre-registered falsification rule has already flagged the finding as weak — the result card must surface this, not bury it.

(c) Report the canonical-case synthetic controls for CHN, IND, NZL, VNM alongside a second set for the known-weak cases (GHA, ZMB, KEN, MEX late-1980s) so readers see the full distribution.

(d) Acknowledge the Rodrik 2006 critique explicitly and note that the hypothesis cannot distinguish trade-liberalisation-specific effects from bundled-reform effects. A cleaner identification (e.g., WTO-entry-cohort timing as a source of quasi-experimental variation, as Grossman-Helpman and later Baier-Bergstrand have done with gravity models) belongs to a v2.

The strongest version of the steelman points at a different hypothesis entirely: the growth gains attributed to liberalisation belong to the bundled institutional package, and the marginal product of trade opening (holding institutions constant) is much smaller than the canonical cases suggest. If the framework can't distinguish these, it should say so.
