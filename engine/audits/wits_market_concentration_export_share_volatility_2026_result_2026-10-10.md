# Earlier export-market concentration and later export-share volatility — frozen result

**Verdict: PARTIAL.** One prospectively registered descriptive test. Complete economies: 124 of 149 source-key candidates.
Material HHI changes: 43; HHI change IQR: 0.055734807.
Beta: 0.27336618 export/GDP-share volatility points per +0.1 prior market HHI change; HC3 SE: 0.38842768; two-sided p: 0.48294694.
Maximum residualized exposure share: 0.12719647; maximum residualized outcome share: 0.15510675; leave-one-out successes: 124; failures: 0.
Failed gates: none.

The local WITS series id says product_concentration, yet its source indicator is HH-MKT-CNCNTRTN-NDX, the export-**market** Herfindahl-Hirschman concentration index. It measures concentration across destination partners, not export products. The archived wits_export_product_diversification_resilience_panel generic screen was PARTIAL and mislabeled this market series as product concentration. No old verdict is relabeled or regraded.

The WDI outcome is the sample standard deviation of ten annual changes in exports of goods and services as a percentage of GDP, from 2011 through 2020. Changes in the GDP denominator, services outside the WITS merchandise index, and the 2020 pandemic shock limit interpretation. Neither the predictor nor outcome identifies a trade-policy effect or a causal mechanism. No causal, policy, school, position, or featured credit follows. The nominal 0.01 cutoff does not correct the wider archive's model selection.

The WITS fetch manifest lists World Bank WITS terms; raw WITS values are not copied into tracked artifacts. Exact replay requires the hash-pinned vintage and its source terms.

Definitions: [WITS market concentration index](https://wits.worldbank.org/WITS/WITS/TradeIndicatorsHelp/TradeOutcomes_Help.htm?AspxAutoDetectCookieSupport=1); [World Bank exports of goods and services/GDP](https://data.worldbank.org/indicator/NE.EXP.GNFS.ZS).
