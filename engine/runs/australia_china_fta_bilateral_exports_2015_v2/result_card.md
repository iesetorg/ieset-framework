# australia_china_fta_bilateral_exports_2015_v2

**Verdict: INCONCLUSIVE** — registered pretrend gate failed

Measured dyad: AUS → CHN. This is a descriptive merchandise-flow comparison, not a causal treaty effect.

- Agreement effective: 2015-12-20 (https://www.dfat.gov.au/trade/agreements/in-force/chafta/australia-china-fta).
- Pre: 2011–2014; post: 2016–2019; 2015 excluded from means.
- Donor origins to CHN: USA, CAN, JPN, TWN, IND, DEU, FRA, ITA.
- CEPII source archive SHA-256: 7ffea0510a536587f2f9295bbafef4a312a36b366acc256eb6d9770fe35e44b1.
- Committed slice SHA-256: 8e0e6eab245bed9597a3d393f2cf9e80518d1d674e5867989f0a895f60657e92.
- Registration commit: f19aefa6a75e416b80031d01d6ae4a9617481e20.
- Slice commit: 4c031ade5db66a1ec2b5fdb3c01fa8ba67dd2374.
- Family size: five fixed treaty tests; no optional reverse-direction or product result.
- School and policy score credit: zero.
- Old result disclosed: trade_lib_chafta_australia_china_2015 was PARTIAL on a different WDI country-outcome design.
- Pretrend slope gap: 0.038806 log units/year; maximum absolute gap 0.030000.

## Limits

BACI values are nominal goods trade in thousands of current US dollars; they mix prices and quantities. CEPII fta_wto records agreement status, not tariff intensity. Iron ore and other commodity prices, Chinese demand and contemporaneous North Asian FTAs confound the contrast; 2020 is excluded. The fixed donor set and pretrend screen do not remove remaining confounding.

Reproduce: python3 scripts/run_fta_baci_five_event_family_2026.py verify --case australia_china_fta_bilateral_exports_2015_v2
