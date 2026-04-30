# Steelman — LatAm remittance dependency / dollarisation pull 2020-2025

**The strongest argument against the associational claim:**

The hypothesis is that remittance-share-of-GDP growth 2019-2024 is positively associated with
resident-deposit USD-share growth across non-dollarised LatAm economies, and that incomplete
US-Fed-rate pass-through reinforces the dollarisation pull. The opposing view is that
dollarisation dynamics are dominated by domestic inflation-credibility history (Levy-Yeyati
2006) and that remittance flows pass through retail-cash channels rather than into the formal
banking system, producing minimal direct effect on deposit-currency composition.

Specific objections the hypothesis must engage:

1. **Remittances are largely consumption-spent, not saved.** Remittance recipients are
   predominantly low-income households who consume the inflows immediately on food, housing,
   utilities, and remittance-corridor fees. The fraction of remittances saved in formal-bank
   USD accounts is small. Even a doubling of remittance flows would have a small effect on
   deposit composition because the flow is short-cycle. The hypothesis's deposit-share-of-USD
   metric may be insensitive to the actual channel.

2. **Cross-section power is severely limited.** With n=5 non-dollarised LatAm countries
   (MEX, GTM, HND, NIC, DOM), the cross-section regression has effectively no statistical
   power to detect a 0.15 coefficient with confidence. The panel-FE specification with
   country fixed effects relies on within-country time variation, which for slow-moving
   variables like deposit dollarisation is also limited. The hypothesis may be statistically
   underpowered.

3. **IMF FSI deposit-dollarisation data has gaps.** Coverage of resident-deposit USD-share
   varies by country and reporting cycle. Mexico publishes detailed monthly data via
   Banxico; Honduras and Guatemala publish annual data with lags; Nicaragua's reporting
   has deteriorated. The dependent-variable measurement quality varies across panel units,
   and the variation is correlated with the exposure variable (remittance-dependent countries
   tend to have weaker financial-statistics infrastructure).

4. **US-Fed pass-through gap is not unique to remittance recipients.** The 2022-2023 Fed
   hiking cycle produced incomplete pass-through to local deposit rates across most of
   emerging Latin America (Brazil, Chile, Colombia all show real-rate gaps), not just the
   remittance-dependent six. Attributing the local-rate vs Fed-rate gap to the remittance
   channel is over-attribution; the underlying mechanism is general EM-monetary-policy
   independence dynamics.

5. **Mexican remittance growth has structural drivers unrelated to USD-pull.** The 2020-2023
   Mexican remittance surge (~$36bn → ~$63bn) is partly driven by Mexican-emigrant labour-market
   improvements, partly by exchange-rate dynamics (peso appreciation made USD-denominated
   transfers more attractive in peso terms), and partly by formalisation of previously
   informal flows post-2020. Treating it as a single "remittance-pull" treatment ignores
   substantial composition effects.

**How this steelman should shape the result card:**

The v1 result card must:

(a) Report the panel-FE coefficient with its 90% confidence interval prominently —
    statistical-power constraints mean a "not-informative" verdict (CI spans 0) is the most
    likely outcome and that should be flagged transparently.

(b) Decompose remittance flows into formal-bank vs cash-corridor channels where data permits
    (Mexico's Banxico publishes this; others rely on World Bank Remittance Prices indirect
    estimates).

(c) Compare the LatAm-six pattern to a similar group of remittance-dependent non-LatAm
    economies (Philippines, Bangladesh, Egypt, Morocco) where remittance flow growth has
    not co-occurred with the same rate-cycle. This out-of-sample test would distinguish
    remittance-channel from EM-monetary-policy-channel.

(d) Track local-currency-deposit real rates against US Fed rate explicitly so the pass-through
    gap is documented separately for each country, not pooled.

(e) Accept that the most likely v1 verdict is "not informative due to power constraints"
    and that a v1.1 spec extending the sample to include all remittance-dependent
    middle-income economies globally would be a stronger second-attempt design.
