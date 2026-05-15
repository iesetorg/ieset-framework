# Result card - frontier_real_wage_growth_market_competition_1980_2024

**Verdict:** PARTIAL - proxy-only local rerun does not clear the registered positive/significant wage and productivity thresholds

## Pre-registration
- **Claim:** Across OECD and high-income economies 1980-2024, real wage growth at the productivity frontier is stronger in countries with more competitive product markets and lower barriers to firm entry. The pre-registered claim is that a one-standard-deviation improvement in product-market competition is associated with at least 0.4 percentage points higher annual real wage growth and at least 0.3 percentage points higher labour-productivity growth, after controlling for initial income, trade openness, union density, and sectoral composition.
- **Falsification rule:** Not supported if (a) the coefficient on product-market competition is not positive and significant at p<0.05 on real wage growth, OR (b) the coefficient is not positive and significant at p<0.05 on labour- productivity growth, OR (c) the implied effect of a one-SD competition improvement on real wage growth is below 0.20 pp/year. A "monopsony- power / rent-sharing" reading wins if coefficients are negative (suggesting more competition hurts worker bargaining power).
- **Falsification test:** panel_fe_product_market_competition_on_real_wage_growth

## Proxy Design
- Outcome proxy: OECD PDB nominal labour compensation per hour growth (LCHRS, total economy) minus WDI CPI inflation.
- Productivity outcome: OECD PDB GDP per hour worked growth (GDPHRS, chain-linked volume, total economy).
- Treatment: 0.6 * inverted OECD PMR overall z-score + 0.4 * Fraser EFW regulation z-score, re-standardised so one unit is one sample SD.
- Controls fitted: log GDP per capita, trade openness, union density, services share of GDP; real interest is documented but omitted for sparse coverage.

## Estimates
| outcome | beta per 1 SD competition | p-value | observations | countries | years |
|---|---:|---:|---:|---:|---|
| real_wage_growth_proxy | -5.285 | 0.685 | 47 | 29 | 2018, 2023 |
| labour_productivity_growth | -5.848 | 0.444 | 47 | 29 | 2018, 2023 |

## Interpretation
This proxy-only screen does not support the registered positive/significant threshold. The wage proxy coefficient is negative and not significant, and the productivity coefficient is also negative and not significant in the complete-control specification. Because the exact wage outcome and broader PMR coverage are still absent, this remains research-only rather than a dispositive refutation.

## Source Paths
- `OECD PDB: compensation and productivity` -> `data/vintages/oecd/DSD_PDB@2026-05-12T133454Z.parquet`
- `OECD PMR overall index` -> `data/vintages/oecd_pmr/PMR@2026-05-05T200616Z.parquet`
- `OECD PMR barriers to entry` -> `data/vintages/oecd_pmr/BARRIER_ENTRY@2026-05-02T220000Z.parquet`
- `Fraser EFW regulation area` -> `data/vintages/fraser_efw/regulation@2026-05-02T220000Z.parquet`
- `OECD trade union density` -> `data/vintages/oecd/TUD@2026-05-05T195705Z.parquet`
- `WDI CPI inflation` -> `data/vintages/world_bank_wdi/FP.CPI.TOTL.ZG@2026-04-30T135619Z.parquet`
- `WDI real GDP per capita` -> `data/vintages/world_bank_wdi/NY.GDP.PCAP.KD@2026-04-30T113730Z.parquet`
- `WDI trade openness` -> `data/vintages/world_bank_wdi/NE.TRD.GNFS.ZS@2026-05-05T194657Z.parquet`
- `WDI services share of GDP` -> `data/vintages/world_bank_wdi/NV.SRV.TOTL.ZS@2026-05-05T195011Z.parquet`
- `WDI real interest rate` -> `data/vintages/world_bank_wdi/FR.INR.RINR@2026-04-30T102408Z.parquet`

## Caveats
- Proxy-only: OECD PDB labour compensation per hour deflated by WDI CPI replaces the unavailable OECD average-wage real-growth series.
- OECD earnings vintages on disk are wage-gap tables, not average annual wages, so they are not used as the wage outcome.
- PMR overall and barriers-to-entry coverage in local vintages is limited to 2018 and 2023.
- WDI real interest rate is documented but excluded from the fitted model because it leaves only 16 complete observations.
- Result should remain research_only, not a scoreboard candidate, unless exact wage series and wider PMR coverage are added.
