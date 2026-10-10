# JST prior fiscal-share forward family: frozen source plan

Date: 2026-10-10. This first-registration packet precedes selected outcome value and null-mask access. It is one descriptive eight-outcome research family, not eight independent replications and not a policy or causal test.

## Source identity and rights

- JST Macrohistory R6: `data/vintages/jst/jst_r6@2026-04-30T114353Z.parquet`, SHA-256 `4219d53e595e50b05430b5e4edd91f5f9ebff3987e3d0b6f21d2f2f50bc03a6f`.
- Original publisher file: https://www.macrohistory.net/app/download/9834512569/JSTdatasetR6.xlsx
- Publisher documentation: https://www.macrohistory.net/database/
- Local fetch manifest: `data/manifests/fetch_run_2026-04-30T105817Z.yaml`.
- License: CC BY-NC-SA 4.0; no source, row-level, or country-level values will enter the tracked packet. Public use needs a separate rights review. Cite Jordà, Schularick and Taylor (2017), *Macrofinancial History and the New Business Cycle Facts*.
- Historical R6 nominal expenditure, revenue and GDP are in local currency; divide like-valued levels to form percent-of-GDP exposure and control. This is not expenditure *composition*, a fiscal shock, or an intervention.

## Prior-only source preflight

The exact JST file has 2,718 annual rows, 18 country codes, years 1870–2020, unique country/year keys. The fixed source-key grid requires 702 keys covering t−1, t and t+5 for 18 anchors in 18 countries; every key exists. No selected outcome value or null mask was read. Only prior-year nominal expenditure, revenue, GDP and their derived ratios were opened: 312 of 324 candidate country-anchor cells are finite and in the registered [-10,100]% ratio range, across all 18 countries. Prior-only residualization of expenditure share against revenue share, country and anchor effects is full rank (37/37); residual exposure SD is 2.885 pp, largest country share 0.1923, largest top-one-percent-row share 0.2535. These descriptive preflight numbers are not a result and do not set or adjust post-outcome thresholds.

Anchors are `[1900, 1905, 1920, 1925, 1930, 1950, 1955, 1960, 1965, 1970, 1975, 1980, 1985, 1990, 1995, 2000, 2005, 2010]`. The omitted 1910–15 and 1935–45 anchor windows would cross the World Wars. Fixed response t→t+5; treatment and revenue control at t−1. Do not choose replacement years, countries, horizons, vintages, or outcomes after measurement.

## Frozen family

Eight outcomes, in this order: gdp_pc_growth, consumption_pc_growth, investment_share_change, unemployment_change, cpi_inflation, short_rate_change, long_rate_change, current_account_share_change. GDP and consumption use annualized five-year log growth in percentage points; investment share, unemployment, short and long rates, and current-account/GDP share use exact five-year percentage-point changes; CPI uses annualized five-year log inflation. Exact formulas, endpoint range rules and practical magnitudes are in the eight immutable specs and runner.

Each cell must have ≥180 complete pairs, ≥14 countries, ≥14 anchors, ≥8 complete anchors for each retained country, and ≥12 anchors each with ≥10 countries. Country/anchor fixed-effect OLS includes prior revenue/GDP. Require full rank, finite positive CR1 country-cluster SE and two-sided t(G−1) p, residualized spending SD≥1.0 pp, outcome residual SD at least its fixed cell threshold, maximum country share of residualized expenditure variation≤25%, maximum top 1% row share≤30%, and all leave-one-country-out fits finite/full rank. A failed gate yields INCONCLUSIVE even if a diagnostic coefficient exists.

Directional SUPPORTED/REFUTED requires the fixed practical slope in the predicted/opposite direction, Bonferroni-adjusted two-sided p≤0.01 over all eight cells (raw p≤0.00125), and every country-deletion slope retaining that sign. Other estimable outcomes are PARTIAL. The family contains eight tests regardless of inconclusive cells. No school, position, featured, causal, or policy credit.

## Distinctness and interpretation

This exposure is historical total nominal expenditure/GDP in t−1. Existing generic WDI/Heritage government-spending panels and JST investment-share, term-spread, mortgage-share, current-account-deficit, and credit families ask different source/estimand questions. Their previous results are visible; they confer no credibility or directional prior on this test. The eight responses share historical sources and macro shocks. Fixed effects and timing do not remove reverse expectations, denominator mechanics, fiscal automatic stabilizers, changing national institutions, or wartime/Depression context.

Required sequence: first commit all eight specs, steelmans, this plan and runner; commit one metadata source lock per cell in fixed order; only then read selected outcome columns, write result packets, commit them, exact-replay all artifacts, and refresh evidence indexes. If a frozen gate fails, retain INCONCLUSIVE without changing the threshold or sample.
