# DPRK manual data — provenance

This directory holds reconstructed DPRK data used by canonical-case
multi-metric runs. DPRK does not publish national accounts, vital
statistics, customs data, or telecoms statistics. All estimates are
external reconstructions from cross-referenced methodologies.

## Files

### `bok_gdp_estimates.yaml`
- **Source:** Bank of Korea (BOK), "Gross Domestic Product Estimates of
  North Korea" annual press release series.
- **URL:** https://www.bok.or.kr/eng/main/contents.do?menuNo=400084
- **Methodology:** Physical-output reconstruction + trade-mirror;
  released July of year *t+2*.
- **Citation:** Bank of Korea (BOK). 2002–2024. *Gross Domestic Product
  Estimates of North Korea in [year]*. Seoul: Bank of Korea.
- **License:** Public press release.
- **Vintage drop date:** 2026-04-24.

### `eberstadt_2010_indicators.yaml`
- **Source:** Eberstadt, Nicholas. 2010. *Policy and Economic Performance
  in Divided Korea during the Cold War Era: 1945–91*. AEI Press, with
  selected post-2000 updates from his AEI papers and the
  *Korean Journal of Defense Analysis* series.
- **Coverage:** DPRK mortality (infant, under-5), nutrition (caloric
  intake per capita), electricity (kWh per capita), cement-equivalent
  proxy for industrial output. ROK comparators where co-reported.
- **Methodology:** UN, FAO, IEA cross-references plus refugee-testimony
  triangulation; cement-equivalent uses a cement-tonnage-vs-GDP elasticity
  benchmarked against East Asian peers.
- **License:** Author quote with citation; no data-redistribution constraint
  beyond academic citation.

### `goodkind_west_dprk_famine_mortality.yaml`
- **Source:** Goodkind, Daniel, and Loraine West. 2001. "The North Korean
  Famine and Its Demographic Impact." *Population and Development Review*
  27(2): 219–238. With the 2011 update by Goodkind, West & Johnson on
  the 2008 DPRK census reconciliation.
- **Methodology:** Cohort-survival demographic accounting using the 1993
  and 2008 DPRK censuses (UNFPA-supervised) plus pre-famine fertility
  baselines. Central estimate 600k–1m excess deaths 1995–2000.

### `spoorenberg_schwekendiek_dprk_demography.yaml`
- **Source:** Spoorenberg, Thomas, and Daniel Schwekendiek. 2012.
  "Demographic Changes in North Korea: 1993–2008." *Population and
  Development Review* 38(1): 133–158.
- **Methodology:** Cohort reconstruction from UNFPA census microdata,
  reconciled with international migration estimates.

### `pak_2004_dprk_heights.yaml`
- **Source:** Pak, Sunyoung. 2004. "The biological standard of living in
  the two Koreas." *Economics & Human Biology* 2(3): 511–521.
- **Methodology:** Adult male/female stature comparison using ROK
  conscript records and DPRK refugee anthropometric measurements.

### `schwekendiek_2009_anthropometric_reconstruction.yaml`
- **Source:** Schwekendiek, Daniel. 2009. "Height and weight differences
  between North and South Korea." *Journal of Biosocial Science* 41(1):
  51–55.
- **Methodology:** Refugee-sample anthropometry corrected for
  selection bias.

### `henderson_storeygard_weil_2012_nightlights_gdp.yaml`
- **Source:** Henderson, J. Vernon, Adam Storeygard, and David N. Weil.
  2012. "Measuring Economic Growth from Outer Space." *American Economic
  Review* 102(2): 994–1028. With Nordhaus, William. 2006. "Geography
  and macroeconomics: New data and new findings." *PNAS* 103(10): 3510–3517,
  for the night-lights-as-GDP-proxy validation.
- **Companion satellite source:** NOAA DMSP-OLS (1992–2013) and VIIRS
  Day/Night Band (2012–present). https://eogdata.mines.edu/products/vnl/
- **Methodology:** Per-area radiance inferred from annual stable-lights
  composites; ROK/DPRK per-area ratio computed from the canonical DMZ
  border imagery.

### `fortune_global_500.yaml`
- **Source:** Fortune Global 500 annual ranking, https://fortune.com/global500/
  2020–2023 issues.
- **License:** Editorial; per-firm citation permitted.

### `rok_unification_defector_registry.yaml`
- **Source:** Republic of Korea Ministry of Unification, "Statistics on
  North Korean Defectors" annual release.
  https://www.unikorea.go.kr/eng_unikorea/relations/statistics/defectors/
