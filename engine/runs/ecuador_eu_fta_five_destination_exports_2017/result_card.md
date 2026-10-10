# ecuador_eu_fta_five_destination_exports_2017

**Verdict: INCONCLUSIVE** — registered pooled pretrend gate failed

One EU–Ecuador treaty-level descriptive merchandise-flow comparison, not a causal effect.

- Provisional application: 2017-01-01 ([Official Journal](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:22016X1229(02))).
- ECU exports to DEU, ESP, FRA, ITA, NLD; donors ARG, BOL, BRA, PRY, URY.
- Pre 2012–2015, post 2017–2019; 2016 omitted from averages.
- CEPII archive SHA-256: 7ffea0510a536587f2f9295bbafef4a312a36b366acc256eb6d9770fe35e44b1.
- Committed slice SHA-256: 1c1c990a40da4aecd8b6d12761f3dacd525075c6e7d106d0b8b3326750160df7.
- Registration commit: f8902503c41d697984359ca6c0a6c62627e819b9.
- Source-slice commit: 2b705da13152cae82344dd4dd30ec9e59240b423.
- Family size: one pooled test; destination components are diagnostics only.
- Causal, featured, school, and policy-score credit: zero.
- Pooled pretrend slope: -0.075364 log units/year (absolute maximum 0.030000).

## Limits

Nominal BACI merchandise values mix prices and quantities. CEPII agreement status is not tariff intensity. The 2015–2016 EU preference bridge weakens treatment discontinuity; the 2016 Ecuador earthquake, commodity prices, exchange rates, and partner-specific product mix remain confounders. The same-destination donor comparison and pretrend gate do not identify a treaty effect.

Reproduce: python3 scripts/run_ecuador_eu_fta_2017.py verify
