# new_zealand_china_fta_bilateral_exports_2008_v2

**Verdict: INCONCLUSIVE** — registered pretrend gate failed

Measured dyad: NZL → CHN. This is a descriptive merchandise-flow comparison, not a causal treaty effect.

- Agreement effective: 2008-10-01 (https://www.mfat.govt.nz/assets/Trade-agreements/China-NZ-FTA-Upgrade/China-FTA-Upgrade-NIA.pdf).
- Pre: 2004–2007; post: 2009–2012; 2008 excluded from means.
- Donor origins to CHN: AUS, USA, CAN, JPN, KOR, IND, DEU.
- CEPII source archive SHA-256: 7ffea0510a536587f2f9295bbafef4a312a36b366acc256eb6d9770fe35e44b1.
- Committed slice SHA-256: 8e0e6eab245bed9597a3d393f2cf9e80518d1d674e5867989f0a895f60657e92.
- Registration commit: f19aefa6a75e416b80031d01d6ae4a9617481e20.
- Slice commit: 4c031ade5db66a1ec2b5fdb3c01fa8ba67dd2374.
- Family size: five fixed treaty tests; no optional reverse-direction or product result.
- School and policy score credit: zero.
- Pretrend slope gap: -0.115499 log units/year; maximum absolute gap 0.030000.

## Limits

BACI values are nominal goods trade in thousands of current US dollars; they mix prices and quantities. CEPII fta_wto records agreement status, not tariff intensity. The 2009 global crisis and dairy or timber demand can move New Zealand-China trade; the agreement began late in 2008. The fixed donor set and pretrend screen do not remove remaining confounding.

Reproduce: python3 scripts/run_fta_baci_five_event_family_2026.py verify --case new_zealand_china_fta_bilateral_exports_2008_v2
