# Result card — Chile vs Venezuela divergence, 1999–2023

**Verdict:** SUPPORTED — 2023 log-gap (CHL−VEN) +2.30 (>=1.20). Cumulative growth gap 1999→2023 +1.50 log-points (>=0.60). Chile annualised +2.33%/yr; Venezuela -3.93%/yr.

## Headline numbers

- Series used: WDI `NY.GDP.PCAP.KD` (constant 2015 USD).
- Chile log GDP-pc 1999 → 2023: 9.007 → 9.567; cumulative +0.559 log-points (~+75%); annualised +2.33%/yr.
- Venezuela log GDP-pc 1999 → 2023: 8.210 → 7.266; cumulative -0.944 log-points (~-61%); annualised -3.93%/yr.
- Bilateral log-gap (CHL − VEN): 1999 = +0.798; 2023 = +2.301.
- Cumulative growth gap 1999→2023: +1.503 log-points (~+350% relative).
- Pre-COVID robustness (1999→2019): growth gap +1.248 log-points.

## Threshold applied

- PRIMARY (dispositive): `log_gdp_pc(CHL, 2023) − log_gdp_pc(VEN, 2023) >= 1.20` AND `cumulative_log_growth(CHL, 1999-2023) − cumulative_log_growth(VEN, 1999-2023) >= 0.60`.
- INFORMATIVE: `|log_gdp_pc(CHL, 1999) − log_gdp_pc(VEN, 1999)| < 0.30` (realised: |+0.798|; informative pass: False).

| Component | Threshold | Realised | Pass |
|---|---:|---:|:---:|
| Endpoint log-gap 2023 | >= 1.20 | +2.301 | yes |
| Cumulative growth gap | >= 0.60 | +1.503 | yes |
| Pre-window gap (informative) | < 0.30 | 0.798 | no |

## Interpretation

This is a descriptive bilateral comparison; results are pattern matches, not causal identification. We have not constructed a counterfactual Venezuela or controlled for oil prices, terms-of-trade shocks, or US sanctions. The pre-registered claim is that the magnitude of the divergence is so large that policy content is the most plausible single explanation, but rigorous causal attribution would require a synthetic-control or bilateral DiD design. The Chavismo/Maduro programme overlaps with the 2014 oil price collapse and post-2017 US sanctions, so the gap reflects a bundle of self-inflicted policy and external shocks, not a clean policy-only experiment.

## Sources

- World Bank WDI `NY.GDP.PCAP.KD` (vintage NY.GDP.PCAP.KD@2026-04-28T125340Z.parquet).
- Note: `NY.GDP.PCAP.PP.KD` returns NaN for VEN from 2011 onward in the local WDI vintage; the fallback to constant-USD preserves within-country log-growth comparability.

## Steelman live concerns

See `hypotheses/steelman/chile_vs_venezuela_divergence_1999_2023.md`.
