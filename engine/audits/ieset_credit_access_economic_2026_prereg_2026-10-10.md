# Credit, electricity, and distinct economic outcomes — frozen family preregistration

This is one prospectively selected **descriptive two-test family**. The outcomes are formal limited-liability business-registration density and PWT real household-plus-government consumption per resident. These are distinct constructs, not independent replications of one effect. Both tests stay in the family denominator, including INCONCLUSIVE outcomes. Before this registration, only source bytes and hashes, manifests, schemas, primary definitions, the original PWT variable label, and selected geography/year keys were inspected. No selected values, null masks, derived exposures or outcomes, country rankings, or model fits were opened.

ISO 3166 alpha-3 national-area keys use the fixed pycountry parser. Noncountry aggregates and blank WDI geographies are excluded. Structural key presence does not establish numeric completeness. Raw data stay in the read-only source checkout.

| Role and vintage | SHA-256 | Manifest SHA-256 |
| --- | --- | --- |
| WDI private credit FS.AST.PRVT.GD.ZS 2026-05-05T194720Z | 57d2717d9097b3142f9b116242218621e4560a6bf4e29ddc22081dd66b2a1b19 | a571d660fd359d245176b77e595b59923a90a1e40a799ea56c13f001a7b09945 |
| WDI LLC registrations IC.BUS.NREG 2026-05-05T203439Z | 213a70ca7b1b8259d58f3a3b9e90b9fb84cce3f77b881667f8811a71d25e75ae | 5022cf82e5656d89c54d3c0df1cc3c12718b93896488eebfde3ffa197beef112 |
| WDI population SP.POP.TOTL 2026-05-05T194826Z | 6e8ccda8b27d188d08e0fbf036828c975641453c12e6e68d5807657140cd9456 | a571d660fd359d245176b77e595b59923a90a1e40a799ea56c13f001a7b09945 |
| WDI age-15–64 share SP.POP.1564.TO.ZS 2026-05-05T203617Z | 3099ca75ff53c94c46244648e2efa883dfd391d6c7823ec1cb8a5976ba7e53c2 | 5022cf82e5656d89c54d3c0df1cc3c12718b93896488eebfde3ffa197beef112 |
| WDI electricity access EG.ELC.ACCS.ZS 2026-05-05T195057Z | aa564cbe2947b3d1c3499d7ecb9b2c38c6aa5de073d2cc1a797cfe2fe42f2931 | a571d660fd359d245176b77e595b59923a90a1e40a799ea56c13f001a7b09945 |
| PWT rconna 2026-05-16T114235Z | 79dc9f16f710217ee1cf12d1f10110c90a8f343f48bad113cb972e1d5182fd32 | 489358e15d0f9ab38a824f5f87a4dfe86cbfb2df9009d430589163dd44702b41 |
| Original PWT pwt100.dta | 51d0b44fab4535e2c38ea5b2cab10ede548525e5488b4fafa166776723db4100 | manual source; no fetch manifest |

Original pwt100.dta labels rconna **“Real consumption at constant 2017 national prices (in mil. 2017US$)”**. PWT's primary research documentation identifies RCONNA as household-plus-government consumption at constant national prices. The derived PWT fetch manifest's generic currency field says int_usd_2017_ppp, which conflicts with the original variable label. This design freezes the original label as authoritative and uses only within-country log growth, never cross-country consumption levels. WDI population in persons divides rconna after multiplying its millions scale by 1,000,000. WDI fetch manifests record CC BY 4.0; the PWT manifest records academic_citation. Only aggregate diagnostics and coefficients, when gates pass, are tracked. Chart arrays remain empty.

## Test 1: private credit and formal business entry

The fixed roster has **215** ISO3 national areas with private-credit/GDP keys in 2005 and 2015, and LLC registrations, population, and age-15–64 share keys in 2010, 2015, and 2022. The key-roster file SHA-256 is e9e90739212dd649390f873f3785acbb7d83a28276cf0a861e8d0ac5bc58e37b.

Require finite credit/GDP in [0,500] percent, new LLC registrations in [0,1,000,000,000] count, population >0, and age share in (0,100] percent at each endpoint. Registration density is 1,000 × registrations / (population × age-share/100). Exposure X is credit/GDP in 2015 minus 2005, percentage points. Outcome Y is log1p(density_2022) minus log1p(density_2015). Controls are credit/GDP_2005, log1p(density_2015), and the 2010–2015 log1p density change. Positive beta is the claimed direction. LLC registrations are not all startups or active firms.

## Test 2: electricity access and real consumption per resident

The fixed roster has **180** ISO3 national areas with electricity-access keys in 2000 and 2010 and PWT rconna plus WDI population keys in 2000, 2010, and 2019. The key-roster file SHA-256 is b56b04d9b2c1593cbdeadec2eddf3d068a2c5633adf6bd38a12c0e1d1fa3d665.

Require finite electricity-access share in [0,100] percent, positive PWT rconna at most 1,000,000,000 million 2017 US dollars, and positive WDI population at each endpoint. Real consumption per resident is rconna × 1,000,000 / population. Exposure X is access_2010 minus access_2000, percentage points. Outcome Y is log(consumption per resident_2019) minus log(consumption per resident_2010). Controls are access_2000, log(consumption per resident_2010), and prior 2000–2010 log consumption-per-resident change. Positive beta is the claimed direction. The PWT series includes household and government consumption, not private consumption alone.

## Frozen estimator and gates

For each test, fit one equal-national-area OLS with intercept and three named controls. Use HC3 robust standard error and two-sided Student t reference with N−5 degrees of freedom. No imputation, nearest-year joins, winsorization, geography replacement, alternative model, weighting, subgroup, or post-result covariate choice.

| Test | Minimum complete areas | Material exposure | Minimum material areas | Minimum exposure IQR | Meaningful absolute beta |
| --- | ---: | --- | ---: | ---: | ---: |
| Credit → LLC entry | 90 | absolute credit/GDP change ≥10 pp | 30 | 5 pp | 0.005 log units per +1 pp |
| Electricity → real consumption | 120 | absolute access change ≥10 pp | 30 | 5 pp | 0.002 log units per +1 pp |

Each test additionally requires full rank, residualized exposure and outcome squared sums >1e−10, finite positive HC3 uncertainty, no single area above **15%** of residualized exposure sum of squares or **20%** of residualized outcome sum of squares, and at most **two** failed leave-one-area-out fits. Any gate failure is **INCONCLUSIVE**, without a public coefficient. After all gates pass, **SUPPORTED** requires expected-direction beta at least as large as the meaningful magnitude, two-sided p≤**0.01/2 = 0.005**, and expected sign in at least **80%** of successful leave-one-out fits. **REFUTED** uses the opposite sign with the same magnitude, p, and stability rule. Other estimable outcomes are **PARTIAL**. This local Bonferroni cutoff does not correct wider archive selection.

The scope tags competition_concentration and private_consumption are coarse existing schema categories; the actual measured outcomes are explicitly formal entry density and combined household-plus-government consumption. GDP denominators, demography, registry practice, credit composition, urbanization, income growth, selection, reverse expectations, and common shocks limit interpretation. **Zero causal, policy, school, position, or featured credit** accrues under any verdict.

## Strict chronology and replay

1. Commit this plan, both specs and steelmans, runner, and two key-only rosters before selected numeric access.
2. Verify exact raw bytes, manifests, original PWT label, dimensions, and keys; commit a separate metadata-only family source lock.
3. Only then open selected values, run both fixed designs and gates, and commit the result audit and nine artifacts per test.
4. Regenerate all 18 artifacts and the family audit against original hash-pinned vintages and compare every byte. Refresh shared indexes only after reviewed integration.

Definitions: [WDI domestic credit](https://databank.worldbank.org/metadataglossary/world-development-indicators/series/FS.AST.PRVT.GD.ZS); [WDI new LLC registrations](https://databank.worldbank.org/metadataglossary/world-development-indicators/series/IC.BUS.NREG); [WDI electricity access](https://data.worldbank.org/indicator/EG.ELC.ACCS.ZS); [PWT next-generation paper](https://www.rug.nl/ggdc/docs/the_next_generation_of_the_penn_world_table.pdf).
