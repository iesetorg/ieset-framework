# Legacy archive v2 readiness audit — 2026-10-10

This is a read-only, source-key audit of the **1,320 legacy same-commit**
hypothesis/run pairs. A same-commit result cannot become a strict
preregistration by changing metadata. Any valid v2 needs a separately
committed prospective specification, a new pinned source/holdout boundary,
the frozen estimator and sample gates, a measured run, and public evidence
review. No selected outcome values or outcome null masks were opened for this
triage, and none of the counts below is a conversion.

| Original run-manifest custody | Cases |
| --- | ---: |
| No manifest | 556 |
| Malformed manifest | 1 |
| Parseable, but no source vintages | 39 |
| Vintage references without complete relative path and SHA-256 pins | 521 |
| Every vintage path and SHA-256 pinned | 203 |
| **Total legacy pairs** | **1,320** |

Among the 203 fully pinned pairs, 113 have at least one later pin for the
same source series; 59 have a later pin for every source; only 22 have any
confirmed additional raw calendar year for which both old and new raw files
survive. These are overlapping **upper bounds**, not ready v2 tests. The
added-year evidence collapses to a few series: BIS residential-property
prices (one 2026 quarter), OECD labour-force data (2025), one ECB rate
observation, and a few OECD housing-inequality cells. An inclusive
two-calendar-year key screen reaches 106 of 203; restricting prior sample
end years to 2019 or later leaves 75, still with outcome, claim, and
estimator problems untested.

## Conditional leads and explicit no-go cases

| Case or cluster | Source-key opportunity | Blocking evidence/design issue |
| --- | --- | --- |
| Private credit → manufacturing share cross-school case | 362 2024–25 WDI country-year keys / 181 countries | Existing broad proxy/screening design and same May 2026 vintage; requires a new, coherent v2 question and family rule before outcome access. |
| Trade openness → growth cross-school case | 382 2024–25 keys / 191 countries | Directed pair already has a v2 geographic holdout; duplicate relabel would not add a distinct conversion. |
| Tax revenue → child mortality cross-school case | 316 2024–25 keys / 158 countries | Child-mortality series is modeled and two new years are too short for its claimed capacity mechanism. |
| OECD youth wage gap → youth employment | 38 2023–25 joint keys; only four wage countries in 2025 | Mean/median earnings selector duplication and insufficient cross-country holdout. |
| OECD bargaining coverage → growth penalty | 39 2023–24 keys; none in 2025 | The old p≥0.10 “no penalty” rule is not an equivalence test; requires a new margin and longer holdout. |
| WGI regulatory quality → three-year FDI growth | 59 keys at t=2022 only | One treatment year cannot support the planned country/year fixed-effects validation. |
| BIS household DSR → consumption slowdown | 17 economies and t=2023 only for forward outcome | Later 2026 BIS house-price quarter is not the required consumption outcome. |
| Poland 2017 retirement-age reversal | Later OECD LFS 2025 exists | Existing `demo_pjan` is population, not the stated early-pension take-up measure. |
| Canada disposable-income case | Old manifest has WDI GDP/CPI proxies | Those are not claimed OECD household disposable income. |
| High-bite minimum-wage disemployment | No usable fresh joint source | State teen employment and median-wage bite series are missing. |

The first two WDI clusters merit a bounded *design review*, not bulk
promotion. The rest require new source families, corrected constructs, or
longer independent holdouts. The public target of 500 additional visible
hypotheses cannot be met by relabeling these archives under existing gates.
