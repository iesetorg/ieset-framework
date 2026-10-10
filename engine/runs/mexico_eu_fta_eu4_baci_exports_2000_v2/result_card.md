# mexico_eu_fta_eu4_baci_exports_2000_v2

**Verdict: INCONCLUSIVE** — registered pretrend gate failed

Measured basket: MEX → DEU, FRA, ESP, ITA. This is a descriptive merchandise-flow comparison, not a causal treaty effect.

- Agreement effective: 2000-10 (https://policy.trade.ec.europa.eu/eu-trade-relationships-country-and-region/countries-and-regions/mexico_en).
- Pre: 1996–1999; post: 2001–2004; 2000 excluded from means.
- Donor origins to each EU4 destination: USA, CAN, JPN, KOR, AUS, NZL.
- CEPII source archive SHA-256: 7ffea0510a536587f2f9295bbafef4a312a36b366acc256eb6d9770fe35e44b1.
- Committed slice SHA-256: f88e7db3d08746ed862e2b60ca16103ea56b17fefe222f9be1029ebfa5e1a754.
- Registration commit: d2cafd48c687ab54b54b228835e1d8b94260cb69.
- Slice commit: f2b39bee60ec2e46545c8f5288b114a77aad5921.
- Family size: one fixed treaty test; no optional destination, donor, reverse-direction or product result.
- School and policy score credit: zero.
- Old result disclosed: trade_lib_mexico_eu_fta_2000 was REFUTED on a different WDI country-outcome design.
- Pretrend slope gap: 0.088750 log units/year; maximum absolute gap 0.030000.

## Limits

BACI values are nominal goods trade in thousands of current US dollars; they mix prices and quantities. CEPII fta_wto records agreement status, not tariff intensity. Mexico's NAFTA integration, exchange rates, product mix, and EU4 demand can move nominal goods exports. The fixed donor set and pretrend screen do not remove remaining confounding.

Reproduce: python3 scripts/run_mexico_eu4_baci_2026.py verify --case mexico_eu_fta_eu4_baci_exports_2000_v2
