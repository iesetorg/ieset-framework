# chile_us_fta_bilateral_exports_2004_v2

**Verdict: INCONCLUSIVE** — registered pretrend gate failed

Measured dyad: CHL → USA. This is a descriptive merchandise-flow comparison, not a causal treaty effect.

- Agreement effective: 2004-01-01 (https://ustr.gov/issue-areas/industry-manufacturing/industrial-tariffs/free-trade-agreements).
- Pre: 2000–2003; post: 2005–2008; 2004 excluded from means.
- Donor origins to USA: ARG, BOL, BRA, ECU, PRY, URY, VEN.
- CEPII source archive SHA-256: 7ffea0510a536587f2f9295bbafef4a312a36b366acc256eb6d9770fe35e44b1.
- Committed slice SHA-256: 8e0e6eab245bed9597a3d393f2cf9e80518d1d674e5867989f0a895f60657e92.
- Registration commit: f19aefa6a75e416b80031d01d6ae4a9617481e20.
- Slice commit: 4c031ade5db66a1ec2b5fdb3c01fa8ba67dd2374.
- Family size: five fixed treaty tests; no optional reverse-direction or product result.
- School and policy score credit: zero.
- Old result disclosed: trade_lib_chile_bilateral_fta_cascade was REFUTED on a different WDI country-outcome design.
- Pretrend slope gap: 0.068868 log units/year; maximum absolute gap 0.030000.

## Limits

BACI values are nominal goods trade in thousands of current US dollars; they mix prices and quantities. CEPII fta_wto records agreement status, not tariff intensity. Chile signed several other FTAs around 2004, and copper prices and export composition can change nominal flow. The fixed donor set and pretrend screen do not remove remaining confounding.

Reproduce: python3 scripts/run_fta_baci_five_event_family_2026.py verify --case chile_us_fta_bilateral_exports_2004_v2
