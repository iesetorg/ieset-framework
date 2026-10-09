# australia_korea_kafta_bilateral_exports_2014

**Verdict: INCONCLUSIVE** — registered pretrend gate failed

Measured dyad: AUS → KOR. This is a descriptive merchandise-flow comparison, not a causal treaty effect.

- Agreement effective: 2014-12-12 (https://www.dfat.gov.au/trade/agreements/in-force/kafta/korea-australia-fta).
- Pre: 2010–2013; post: 2015–2018; 2014 excluded from means.
- Donor origins to KOR: RUS, BRA, ARG, ZAF, SAU, MEX.
- CEPII source archive SHA-256: 7ffea0510a536587f2f9295bbafef4a312a36b366acc256eb6d9770fe35e44b1.
- Committed slice SHA-256: 6f28b6b58e23368bc20e8ae4edfc6c126d2a3e880a4ee68b326d5eb316d6947b.
- Registration commit: 875a73edf028d4cc191697389872fefbc6268772.
- Slice commit: 34be6d7ada44e4390de1304e863979ff619ed361.
- Family size: two fixed treaty tests; no optional reverse-direction or product result.
- School and policy score credit: zero.
- Pretrend slope gap: -0.102133 log units/year; maximum absolute gap 0.030000.

## Limits

BACI values are nominal goods trade in thousands of current US dollars; they mix prices and quantities. CEPII fta_wto records agreement status, not tariff intensity. This is a separate agreement within the recorded Australia North Asia bundle. The earlier AUS>CHN ChAFTA direct-flow test was INCONCLUSIVE on pretrend, and the old ChAFTA WDI result was PARTIAL; both were known before this registration. Korean demand, commodity prices, Australia's terms of trade and Korea's own simultaneous FTAs can move nominal exports. The fixed donor set and pretrend screen do not remove remaining confounding.

Reproduce: python3 scripts/run_fta_baci_two_north_asia_event_family_2026.py verify --case australia_korea_kafta_bilateral_exports_2014
