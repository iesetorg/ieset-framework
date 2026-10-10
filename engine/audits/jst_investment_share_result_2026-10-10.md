# Measured audit: JST investment share and future living standards

## Custody and decision boundary

The first registration commit is `a68fb090dbab5491144895834b34ed324c7b6588`. Twenty metadata-only source locks were separately committed in frozen runner order; the final lock is `0e85e60b581d1d49576151133bdc98e86a0dc228`. The exact source SHA-256 and 450-key roster were verified before selected measurements were opened. Each packet records its own lock commit and the same fixed 20-member Holm family. The registration, source-lock chronology, and measured packets are distinct Git stages. Licensed raw or country-level JST measurements were not committed.

Frozen verdicts: **13 PARTIAL, 6 INCONCLUSIVE, 0 SUPPORTED, 1 REFUTED**. The 14 complete, ungated measurements are eligible only as descriptive public calibrations after the independent evidence-tier audit. The 6 gated cells remain archive. These twenty correlated cells are one substantive family and are not twenty independent replications. No result grants causal, policy, school, position, or featured credit.

| Era | Outcome | Complete countries / anchors | Slope per investment-share pp | Raw p | Holm p | Verdict / gate |
|---|---|---:|---:|---:|---:|---|
| 1890–1910 | gdp_pc_growth | 15 / 60 | -0.2326 | 0.218017 | 1 | PARTIAL |
| 1890–1910 | consumption_pc_growth | 15 / 60 | -0.2383 | 0.265181 | 1 | PARTIAL |
| 1890–1910 | real_wage_growth | 15 / 60 | +0.0127 | 0.908807 | 1 | PARTIAL |
| 1890–1910 | unemployment_change | 6 / 23 | — | — | 1 | INCONCLUSIVE (country_floor, country_anchor_floor, anchor_floor) |
| 1920–1940 | gdp_pc_growth | 15 / 58 | -0.2237 | 0.11384 | 1 | PARTIAL |
| 1920–1940 | consumption_pc_growth | 15 / 58 | +0.0052 | 0.972379 | 1 | PARTIAL |
| 1920–1940 | real_wage_growth | 15 / 57 | -0.2416 | 0.121589 | 1 | PARTIAL |
| 1920–1940 | unemployment_change | 11 / 39 | — | — | 1 | INCONCLUSIVE (country_floor, country_anchor_floor, anchor_floor) |
| 1950–1970 | gdp_pc_growth | 18 / 71 | -0.0634 | 0.304534 | 1 | PARTIAL |
| 1950–1970 | consumption_pc_growth | 18 / 71 | -0.0556 | 0.303079 | 1 | PARTIAL |
| 1950–1970 | real_wage_growth | 18 / 71 | +0.2124 | 0.153362 | 1 | PARTIAL |
| 1950–1970 | unemployment_change | 17 / 67 | +0.0938 | 0.0534103 | 0.961386 | PARTIAL |
| 1975–1995 | gdp_pc_growth | 18 / 72 | -0.0947 | 0.120644 | 1 | INCONCLUSIVE (country_exposure_concentration) |
| 1975–1995 | consumption_pc_growth | 18 / 72 | -0.1313 | 0.062338 | 1 | INCONCLUSIVE (country_exposure_concentration) |
| 1975–1995 | real_wage_growth | 18 / 72 | -0.0278 | 0.737972 | 1 | INCONCLUSIVE (country_exposure_concentration) |
| 1975–1995 | unemployment_change | 18 / 72 | +0.2997 | 0.212846 | 1 | INCONCLUSIVE (country_exposure_concentration) |
| 2000–2020 | gdp_pc_growth | 18 / 72 | -0.1848 | 0.0766955 | 1 | PARTIAL |
| 2000–2020 | consumption_pc_growth | 18 / 71 | -0.0931 | 0.0362509 | 0.688768 | PARTIAL |
| 2000–2020 | real_wage_growth | 18 / 72 | +0.0248 | 0.775036 | 1 | PARTIAL |
| 2000–2020 | unemployment_change | 18 / 72 | +0.8318 | 4.00655e-06 | 8.01309e-05 | REFUTED |

## Interpretation

The sole refutation is the 2000–2020 unemployment-change prediction: the fitted slope is positive 0.8318 unemployment percentage points per one percentage point higher starting investment share, opposite the registered negative sign, with Holm-adjusted p=0.0000801 and all country-deletion slopes in the opposite direction. It remains descriptive; the period includes crisis and pandemic shocks, and the investment ratio is endogenous.

The 1890–1910 and 1920–1940 unemployment cells fail the country/anchor completeness floors. Every 1975–1995 cell has sufficient complete coverage but exceeds the frozen maximum share of residualized exposure variation from one country. Those cells remain INCONCLUSIVE despite fitted slope and p-value diagnostics. No sample repair, gate change, replacement vintage, or additional test was used after the result.

All other complete cells are PARTIAL under the frozen effect, twenty-test Holm, and deletion rules. Correlation among real GDP, real consumption, wages, and unemployment is not independent confirmation. The source is the [Jordà–Schularick–Taylor Macrohistory Database R6](https://www.macrohistory.net/database/) (CC BY-NC-SA 4.0), cited as Jordà, Schularick and Taylor (2017). Exact replay requires a lawfully held source copy with the pinned SHA-256.

## Reproduction

Run `python3 scripts/run_jst_investment_share_2026.py verify --source-parquet <local-JST-R6-parquet>` from this checkout after the result commit. The command rechecks the historical schema, registration bytes, all source-lock ancestry and bytes, fixed source/key hash, twenty measured diagnostics, and every evidence-packet byte.
