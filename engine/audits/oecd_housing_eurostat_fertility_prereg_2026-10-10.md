# OECD housing overburden and later fertility: frozen registration

Registered before selected Eurostat fertility values, missingness, or model fits were opened. The preflight read OECD exposure values and statuses plus Eurostat country/year/indicator keys only. Both pinned files predated this registration within the broader IESET corpus; this is not an independent future-data holdout.

## Fixed question and sample

OECD How's Life 3_3 PT_POP low-income housing-cost overburden change t−3→t (anchors 2013–2019) predicts Eurostat demo_find TOTFERRT change t→t+3. Exact normal-status housing observations are required for all four exposure years; country enters only with at least two eligible anchors. The key-only roster has **118 pairs in 24 countries**; 63 pairs in 23 countries have at least 2 percentage points of absolute exposure change. These are upper bounds, not observed fertility coverage.

## Frozen analysis

Outcome is three-year fertility change in births per woman. OLS includes baseline housing burden at t−3, baseline fertility at t, country effects and anchor-year effects. Inference uses country-cluster CR1 and two-sided Student t(G−1). Complete-case floors are 95 pairs/20 countries and 50 material pairs/18 countries. Residualized exposure must be nonzero; the two largest squared-residual rows may contribute at most 30%, and the largest country at most 25%. Full rank and finite positive clustered uncertainty are required. The 2013–2016 pre-pandemic sign check requires 45 pairs/14 countries. SUPPORTED requires beta≤−0.003, p≤0.01 and negative pre-pandemic beta; REFUTED requires beta≥+0.003, p≤0.01 and positive pre-pandemic beta. Other estimable results are PARTIAL; any primary coverage, concentration or estimator failure is INCONCLUSIVE. No gates change after lock.

## Sources and interpretation

- OECD 3_3 source: `data/vintages/oecd/OECD.ELS.HD_DSD_HH_DASH_DF_HSG_INEQ_1.0@2026-07-23T150432Z.parquet`; SHA-256 `ac7581cb015748d97a21d4feadd08a3afb16cb1d5912af9e0997913ce4db65db`.
- Eurostat TOTFERRT source: `data/vintages/eurostat/demo_find@2026-04-30T115530Z.parquet`; SHA-256 `4db9d291092c0c146aebaa9f3e143b9f9a7a8741f7fc41886e31941aa412c039`.
- Frozen roster SHA-256: `22e167449e554362a42d4126c6346d69a54cd833819d029696e7645e5bdef9b1`.
- [OECD How's Life definitions](https://www.oecd.org/wise/oecd-well-being-database-definitions.pdf): 3_3 is overburden among the bottom-40 income population; the pinned 1.1 parquet labels PT_POP. [OECD Data Explorer](https://data-explorer.oecd.org/vis?bp=true&df%5Bag%5D=OECD.WISE.WDP&df%5Bds%5D=dsDisseminateFinalDMZ&df%5Bid%5D=DSD_HSL%40DF_HSL_CWB&df%5Bvs%5D=1.1&dq=.3_3.._T._T._T.&fc=Topic&fs%5B0%5D=Topic%2C1%7CSociety%23SOC%23%7CWell-being+and+beyond+GDP%23SOC_WEL%23&pd=%2C&pg=0&snb=26&to%5BTIME_PERIOD%5D=false&vw=tb).
- [Eurostat fertility metadata](https://ec.europa.eu/eurostat/cache/metadata/en/demo_fer_esms.htm): TOTFERRT is the sum of period age-specific fertility rates.

This is descriptive calibration only, with zero causal, policy, school-score, position and featured credit. The local p rule does not correct the full IESET archive.
