# korea_us_fta_bilateral_exports_2012_v2

**Verdict: SUPPORTED** — fixed-donor descriptive contrast under the registered gates

Measured dyad: KOR → USA. This is a descriptive merchandise-flow comparison, not a causal treaty effect.

- Agreement effective: 2012-03-15 (https://www.ustr.gov/trade-agreements/free-trade-agreements/korus-fta).
- Pre: 2008–2011; post: 2013–2016; 2012 excluded from means.
- Donor origins to USA: JPN, TWN, CHN, MYS, THA, IDN, VNM, IND.
- CEPII source archive SHA-256: 7ffea0510a536587f2f9295bbafef4a312a36b366acc256eb6d9770fe35e44b1.
- Committed slice SHA-256: 8e0e6eab245bed9597a3d393f2cf9e80518d1d674e5867989f0a895f60657e92.
- Registration commit: f19aefa6a75e416b80031d01d6ae4a9617481e20.
- Slice commit: 4c031ade5db66a1ec2b5fdb3c01fa8ba67dd2374.
- Family size: five fixed treaty tests; no optional reverse-direction or product result.
- School and policy score credit: zero.
- Old result disclosed: trade_lib_korus_2012_us_korea_trade was PARTIAL on a different WDI country-outcome design.
- Pretrend slope gap: 0.017517 log units/year; maximum absolute gap 0.030000.
- Registered contrast: 0.190711 log units (ratio 1.2101); threshold ±ln(1.15).

## Limits

BACI values are nominal goods trade in thousands of current US dollars; they mix prices and quantities. CEPII fta_wto records agreement status, not tariff intensity. Product mix, exchange rates and Korean industrial dynamics can move nominal exports; the post window ends before the 2018 renegotiation. The fixed donor set and pretrend screen do not remove remaining confounding.

Reproduce: python3 scripts/run_fta_baci_five_event_family_2026.py verify --case korea_us_fta_bilateral_exports_2012_v2
