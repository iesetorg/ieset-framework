# Resource Developmentalism Subtype Testability Audit - 2026-05-17

Target: `resource_developmentalism_rent_seeking_trap`

Worker: C

Scope: resource-developmentalism run/audit artifacts only. No movement YAMLs, shared vintage builders, hypothesis YAMLs, result cards, scoreboard files, or broad run artifacts were edited.

## Artifacts Produced

- Run-local validator/prototype: `engine/runs/resource_developmentalism_rent_seeking_trap/subtype_fallback_diagnostics.py`
- Annual subtype sidecar panel: `engine/runs/resource_developmentalism_rent_seeking_trap/resource_developmentalism_subtype_annual_panel_2026-05-17.csv`
- Machine-readable diagnostics: `engine/runs/resource_developmentalism_rent_seeking_trap/subtype_fallback_diagnostics_2026-05-17.json`

The prototype is non-scoring. It validates the existing manual subtype coding, expands it into annual rows, tests clean comparator feasibility, and runs broad-proxy fallback regressions only as diagnostics.

## Verdict

`hold_repair`

The subtype repair is now testable as a sidecar panel, but the cleaned causal score remains blocked. Once `mixed`, `shock`, and `uncoded` years are not allowed to collapse into residual zero controls, the clean treated-versus-comparator sample has no within-country treatment variation under country fixed effects. The preregistered country+year FE design therefore cannot score this sidecar treatment without a redesigned estimator or more within-country episode coding.

The product-export measurement gate is still blocked. A local WITS workbook exists, but it is a URL catalog for annual HHI ZIP payloads, not the underlying country-year data.

## Validation Results

Manual subtype input:

- `data/manual/resource_developmentalism_subtype_coding_2026-05-16.csv`
- SHA256: `70473e24615b82a29697ffd6d5e4f877bd9a000eedb4ea2fd804695e2a0595e6`
- Rows: 106
- Countries: 32
- Episode span: 1961-2026
- Expanded annual rows: 1,348
- Country-year overlaps: 0

1970-2020 coverage after expansion:

| metric | value |
| --- | ---: |
| Annual coded rows | 1,247 |
| Countries | 32 |
| Treated rows | 183 |
| Comparator rows | 221 |
| Shock rows | 13 |
| Excluded rows | 320 |
| Uncoded rows | 510 |
| Clean model rows (`treated` or comparator `yes`) | 332 |
| Clean model countries | 12 |
| Clean treated rows | 183 |
| Clean comparator rows | 149 |

## Generic Scalar Crosswalk

The current `movements:resource_developmentalism` scalar remains too noisy for causal scoring.

Within the 32 manually coded countries over 1970-2020:

| crosswalk bucket | generic-positive rows |
| --- | ---: |
| All generic-positive rows | 540 |
| Promoted to sidecar `treated` | 172 |
| Sidecar comparator | 42 |
| Sidecar excluded/mixed | 316 |
| Sidecar shock | 10 |
| Blocked from clean treatment/control | 326 |

This confirms the previous treatment stop rule in executable form: a majority of generic-positive rows in the reviewed country set should not be interpreted as clean resource-developmentalist treatment.

## Estimability Diagnostics

Two clean samples were tested:

| sample | rows | countries | treated rows | comparator rows |
| --- | ---: | ---: | ---: | ---: |
| Full sidecar clean scope | 332 | 12 | 183 | 149 |
| Original hypothesis country scope only | 231 | 9 | 183 | 48 |

All country+year FE models failed with the same diagnostic:

`treatment 'subtype_treated_any' has no within-country variation under country fixed effects`

This occurred for all three fallback outcomes:

- `export_diversification_index`
- `total_factor_productivity_growth`
- `manufacturing_va_share`

and for both control ladders:

- full controls: `resource_rents`, `initial_gdp_per_capita`, `institutional_quality`
- no-WGI controls: `resource_rents`, `initial_gdp_per_capita`

## Broad-Proxy Descriptive Results

The prototype also ran year-FE-only models as descriptive checks. These are not causal scores and should not be promoted.

Full sidecar clean scope:

| outcome | controls | coef | p-value | n | diagnostic |
| --- | --- | ---: | ---: | ---: | --- |
| Export diversification broad proxy | full | -0.0179 | 0.879 | 165 | not significant |
| Export diversification broad proxy | no WGI | -0.0393 | 0.690 | 258 | not significant |
| TFP growth | full | 0.284 | 0.689 | 150 | not significant |
| TFP growth | no WGI | 0.471 | 0.196 | 255 | not significant |
| Manufacturing VA share | full | 11.764 | 0.0026 | 169 | descriptive positive |
| Manufacturing VA share | no WGI | 11.530 | 0.0025 | 283 | descriptive positive |

Original hypothesis scope only:

| outcome | controls | coef | p-value | n | diagnostic |
| --- | --- | ---: | ---: | ---: | --- |
| Export diversification broad proxy | full | -0.0438 | 0.617 | 112 | not significant |
| Export diversification broad proxy | no WGI | -0.0871 | 0.237 | 193 | not significant |
| TFP growth | full | 0.420 | 0.427 | 95 | not significant |
| TFP growth | no WGI | 0.759 | 0.0199 | 160 | descriptive positive, not causal |
| Manufacturing VA share | full | 12.556 | 0.0001 | 114 | descriptive positive |
| Manufacturing VA share | no WGI | 9.642 | 0.0005 | 188 | descriptive positive |

These descriptive checks do not support promoting the current claim. The export proxy is directionally negative but not significant; TFP is not a negative package; manufacturing share is descriptively higher for treated subtype rows, which is not the preregistered failure channel.

## Measurement Gate Update

Local file found:

- `data/manual/wits/herfindahl_hirschman_product_concentration_index_export_2026-02-09.xlsx`
- SHA256: `f226108714a2a4985854178065edf328797a25a934d3f2ddee76e5fc0707452f`

Workbook status:

- Rows: 69
- Years listed: 1988-2022
- URL rows: 69
- Local payload files: 0
- Usable product/country-year panel: no

This is useful as a fetch manifest, but it is not yet product-level or country-year HHI data. The next measurement step is to download or otherwise acquire the annual ZIP payloads referenced by the workbook, validate their schema, and build a real vintage.

## What This Unlocks

The next run no longer needs to debate the subtype schema. It can consume the annual sidecar panel and the diagnostics JSON directly.

Minimum next-run requirements:

1. Choose an estimator compatible with mostly between-country subtype assignment, or add within-country episode contrasts before keeping country FE.
2. Decide whether the original hypothesis scope should be widened to clean comparator countries such as Norway, Botswana, and Australia, or whether the claim should be narrowed to the original emerging-market scope with very few clean comparators.
3. Fetch and manifest the WITS HHI payloads or another product/concentration source before making product-diversification claims.
4. Keep the old `PARTIAL` result card classified as broad-proxy research-only until both estimator and product measurement gates are repaired.
