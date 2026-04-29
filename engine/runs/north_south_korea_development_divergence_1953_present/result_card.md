# Result card — north_south_korea_development_divergence_1953_present

**Verdict:** supported

**Reason:** 11 of 12 metrics met threshold (support threshold 7)

Pre-registered rule: SUPPORT if >= 7 of 12 metrics met; REFUTE if <= 3 met (impossible to hit support).

**Counts:** 11 MET · 0 NOT_MET · 1 PENDING_DATA · 0 PENDING_EVAL

**Primary country:** KOR

## Metric-by-metric

| # | Metric | Status | Observed | Threshold | Notes |
|---|---|:---:|---:|---|---|
| 1 | gdp_per_capita_ppp_ratio_2023 | MET |  | `>15x ROK/DPRK GDP per capita PPP ratio in 2023` | KOR/PRK ratio = 40.253 @2023 (2023/2023) |
| 2 | life_expectancy_gap_years | MET |  | `>8 year ROK-minus-DPRK life expectancy gap` | KOR-PRK diff = 10.500 @2023 |
| 3 | height_gap_centimetres | MET |  | `>3cm adult male height gap (ROK > DPRK)` | KOR-PRK gap = 5.400 @2015 |
| 4 | internet_penetration_gap | MET |  | `>90 percentage-point ROK-minus-DPRK internet penetration gap` | KOR-PRK diff = 97.100 @2023 |
| 5 | electricity_consumption_per_capita_ratio | MET |  | `>15x ROK/DPRK electricity consumption per capita ratio` | KOR/PRK ratio = 23.333 @2023 (2023/2023) |
| 6 | famine_episode_count | MET |  | `DPRK has >=1 documented peacetime famine event 1953-2023; ROK has 0` | PRK has 40 (2020); threshold >=1; KOR has 0 (2020); threshold >=0 |
| 7 | fortune_global_firm_count | MET |  | `ROK has >=5 Fortune Global 500 firms AND DPRK has 0` | KOR has 18 (2023); threshold >=5; PRK has 0 (2023); threshold >=0 |
| 8 | manufacturing_export_share_world | MET |  | `>100x ROK/DPRK manufacturing export share of world` | KOR/PRK ratio = 350.000 @2023 (2023/2023) |
| 9 | emigration_refugee_asymmetry | PENDING_DATA |  | `Directional asymmetry: DPRK net-emigration + ROK net-immigration sustained >=20 years` | No KOR observations in loaded vintages |
| 10 | patent_filings_ratio | MET |  | `>1000x ROK/DPRK annual patent filings ratio` | KOR/PRK ratio = 4800.000 @2023 (2023/2023) |
| 11 | nightlights_gdp_proxy | MET |  | `ROK/DPRK nightlights radiance per unit area >100x` | KOR/PRK ratio = 141.429 @2023 |
| 12 | infant_mortality_gap | MET |  | `>5x DPRK/ROK infant mortality ratio` | PRK/KOR ratio = 5.375 @2023 (2023/2023) |

## Claim

> From a comparable (arguably DPRK-favoured) 1953 armistice starting point — same ethnicity, language, pre-colonial institutional inheritance, and a Japanese colonial industrial capital stock disproportionately located in the North — the Republic of Korea's market economy with state-directed industrial policy and export discipline, versus the Democratic People's Republic of Korea's autarkic central planning under Juche, produced by 2023 a canonical divergence that pattern-matches >=7 of 10 pre-registered extreme-outcome metrics, each drawn from a different publisher or methodology family. The canonical-case claim is that no other peacetime country pair separated for a comparable duration from a comparable starting point has produced a divergence of this magnitude across this many independent outcome channels. A refutation (<=3 metrics met) would indicate either that the consensus DPRK-ROK gap is materially overstated, or that the framework's institutional-quality coding of market-vs-planned autarky is overstated.

## Interpretation

The canonical-case pattern match is satisfied: 11 of 12 pre-registered metrics meet their thresholds, above the support threshold of 7. Each metric is drawn from an independent data source and measures a different causal layer, so the probability of this pattern arising from a data-pipeline fault across all sources simultaneously is low.

## Steelman live concerns

See `hypotheses/steelman/north_south_korea_development_divergence_1953_present.md` for the strongest opposing arguments. Canonical-case multi-metric evidence is a pattern match, not a causal identification — the result card should be read as 'outcome trajectory matches the predicted pattern to degree X' rather than 'policy P caused the outcome'.

## Provenance

Vintages pinned in `manifest.yaml`. Full per-metric diagnostics in `diagnostics.json`. Machine-readable results in `metric_results.parquet`.
