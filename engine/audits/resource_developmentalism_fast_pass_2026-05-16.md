# Resource Developmentalism Fast-Pass Audit - 2026-05-16

Worker: D, outcome fast-pass lane

Target: `resource_developmentalism_rent_seeking_trap`

Scope discipline: non-persisted analysis only. I imported `scripts/run_panel_fe.py` functions in local scratch commands (`load_spec`, `build_panel`, `filter_sample`, `load_variable`, `run_panel_ols`) and did not overwrite run artifacts, scripts, movement files, hypothesis YAML, or scoreboard files.

## Bottom Line

The current `PARTIAL` result should remain research-only. The fast-pass does not produce a stable, multi-outcome confirmation of the preregistered claim. The primary export-diversification coefficient is sensitive to the control ladder and resource-rich enforcement; TFP growth and manufacturing value-added share do not show the expected negative treatment signal in any robust way.

Decision signal:

| Check | Fast-pass result | Interpretation |
| --- | --- | --- |
| All listed outcomes | Export index moves with specification; TFP and manufacturing do not support the negative long-run claim | Multi-outcome preregistration is not satisfied |
| Full current controls | Reproduces current primary estimate: coef `-0.008`, p `0.758`, n `1320` | Current card is directionally inconclusive |
| Control ladder | Export coefficient is positive and marginal before WGI, then flips to near zero with WGI/listwise deletion | Institutional-quality coverage is driving the estimand/sample |
| Resource-rich enforcement | Country-year `rents >= 5%` plus full controls gives export coef `-0.051`, p `0.005`, but TFP/manufacturing remain null | One fragile primary-outcome signal, not a package result |
| Binary vs intensity | Binary and 0/0.5/1 intensity tell similar null stories under full controls; rent-weighted treatment is not supportive across outcomes | Treatment coding needs redesign before scoring |
| Lag/lead ladder | Export lead terms are as large or larger than current/lag terms in the C2 model | Pre-trend/timing contamination risk |
| Early public-investment channel proxy | Gross capital formation is positive under C2 (`+1.881`, p `0.077`) but weakens with WGI (`+1.292`, p `0.142`) | Some early-gains channel hint, not robust |

Polarity caveat: I followed the existing runner's implied polarity, where a negative coefficient on `export_diversification_index` is treated as consistent with weaker diversification. The underlying proxy is described as Theil/HHI-style broad export concentration. If higher values actually mean greater concentration rather than greater diversification, the sign interpretation must be inverted before any score decision.

## Data And Treatment Coverage

Panel after sample filter: 3,825 country-years, 75 countries, 1970-2020.

| Variable | Nonmissing | Countries | Years |
| --- | ---: | ---: | --- |
| `export_diversification_index` | 2,824 | 74 | 1970-2020 |
| `total_factor_productivity_growth` | 2,681 | 55 | 1970-2019 |
| `manufacturing_va_share` | 2,970 | 72 | 1970-2020 |
| `gross_capital_formation_share` | 3,146 | 70 | 1970-2020 |
| `resource_developmentalism` | 3,825 | 75 | 1970-2020 |
| `resource_rents` | 3,589 | 74 | 1970-2020 |
| `initial_gdp_per_capita` | 3,673 | 75 | 1970-2018 |
| `institutional_quality` | 1,628 | 74 | 1996-2020 |

Treatment values in the loaded vintage are not strictly binary:

| Value | Observations |
| ---: | ---: |
| 0.0 | 3,198 |
| 0.5 | 254 |
| 1.0 | 373 |

Any-positive treatment count: 627 country-years across 34 countries. In the full-control primary export model, this shrinks to 195 treated observations.

## Control Ladder

Treatment is the loaded 0/0.5/1 `resource_developmentalism` intensity. All models use country and year fixed effects with country clustering through the existing runner path.

| Outcome | Controls | Coef | SE | p | n | Countries | Treated obs |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Export diversification index | FE only | 0.055 | 0.035 | 0.114 | 2,824 | 74 | 447 |
| Export diversification index | + resource rents | 0.069 | 0.034 | 0.045 | 2,775 | 74 | 438 |
| Export diversification index | + rents + income | 0.060 | 0.034 | 0.080 | 2,643 | 74 | 423 |
| Export diversification index | + rents + income + WGI rule of law | -0.008 | 0.026 | 0.758 | 1,320 | 73 | 195 |
| TFP growth | FE only | -0.183 | 0.521 | 0.725 | 2,681 | 55 | 418 |
| TFP growth | + resource rents | 0.193 | 0.438 | 0.660 | 2,588 | 54 | 385 |
| TFP growth | + rents + income | 0.135 | 0.426 | 0.751 | 2,535 | 54 | 380 |
| TFP growth | + rents + income + WGI rule of law | 0.128 | 0.755 | 0.865 | 1,076 | 54 | 154 |
| Manufacturing VA share | FE only | -0.692 | 0.815 | 0.396 | 2,970 | 72 | 412 |
| Manufacturing VA share | + resource rents | -0.251 | 0.835 | 0.764 | 2,964 | 72 | 409 |
| Manufacturing VA share | + rents + income | -0.286 | 0.803 | 0.722 | 2,824 | 72 | 394 |
| Manufacturing VA share | + rents + income + WGI rule of law | 0.170 | 0.909 | 0.851 | 1,366 | 72 | 202 |
| Gross capital formation share | FE only | 1.187 | 1.041 | 0.255 | 3,146 | 70 | 454 |
| Gross capital formation share | + resource rents | 1.633 | 1.069 | 0.127 | 3,133 | 70 | 444 |
| Gross capital formation share | + rents + income | 1.881 | 1.064 | 0.077 | 2,999 | 70 | 433 |
| Gross capital formation share | + rents + income + WGI rule of law | 1.292 | 0.879 | 0.142 | 1,357 | 70 | 189 |

Interpretation: WGI rule-of-law coverage roughly halves the sample and flips/attenuates the export coefficient. The listed TFP and manufacturing outcomes remain null under every control ladder.

## Binary Vs Intensity Treatment

`Binary` is `1(resource_developmentalism > 0)`. `Intensity` is the loaded 0/0.5/1 treatment. `Rent-weighted` is intensity multiplied by resource rents and scaled per 10 rent percentage points.

| Outcome | Treatment | Controls | Coef | p | n | Treated obs |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| Export diversification index | Binary | + rents + income | 0.042 | 0.131 | 2,643 | 423 |
| Export diversification index | Intensity | + rents + income | 0.060 | 0.080 | 2,643 | 423 |
| Export diversification index | Rent-weighted | + rents + income | 0.040 | 0.069 | 2,643 | 423 |
| Export diversification index | Binary | Full + WGI | -0.012 | 0.603 | 1,320 | 195 |
| Export diversification index | Intensity | Full + WGI | -0.008 | 0.758 | 1,320 | 195 |
| Export diversification index | Rent-weighted | Full + WGI | 0.010 | 0.644 | 1,320 | 195 |
| TFP growth | Binary | + rents + income | 0.065 | 0.854 | 2,535 | 380 |
| TFP growth | Intensity | + rents + income | 0.135 | 0.751 | 2,535 | 380 |
| TFP growth | Rent-weighted | + rents + income | -0.106 | 0.451 | 2,535 | 380 |
| TFP growth | Binary | Full + WGI | -0.193 | 0.746 | 1,076 | 154 |
| TFP growth | Intensity | Full + WGI | 0.128 | 0.865 | 1,076 | 154 |
| TFP growth | Rent-weighted | Full + WGI | 0.734 | 0.268 | 1,076 | 154 |
| Manufacturing VA share | Binary | + rents + income | -0.183 | 0.792 | 2,824 | 394 |
| Manufacturing VA share | Intensity | + rents + income | -0.286 | 0.722 | 2,824 | 394 |
| Manufacturing VA share | Rent-weighted | + rents + income | 0.161 | 0.574 | 2,824 | 394 |
| Manufacturing VA share | Binary | Full + WGI | 0.405 | 0.603 | 1,366 | 202 |
| Manufacturing VA share | Intensity | Full + WGI | 0.170 | 0.851 | 1,366 | 202 |
| Manufacturing VA share | Rent-weighted | Full + WGI | -0.459 | 0.432 | 1,366 | 202 |

Interpretation: the "binary" preregistered treatment is currently implemented as a graded treatment. Recoding to any-positive binary does not rescue the multi-outcome claim.

## Resource-Rich Sample Enforcement

| Sample | Outcome | Controls | Coef | p | n | Countries | Treated obs |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| Listed-country sample | Export index | + rents + income | 0.060 | 0.080 | 2,643 | 74 | 423 |
| Listed-country sample | Export index | Full + WGI | -0.008 | 0.758 | 1,320 | 73 | 195 |
| Countries ever rents >=5% | Export index | + rents + income | 0.062 | 0.069 | 2,129 | 62 | 423 |
| Countries ever rents >=5% | Export index | Full + WGI | -0.007 | 0.798 | 1,085 | 61 | 195 |
| Countries mean rents >=5% | Export index | + rents + income | 0.071 | 0.099 | 1,355 | 43 | 386 |
| Countries mean rents >=5% | Export index | Full + WGI | -0.013 | 0.631 | 723 | 42 | 187 |
| Country-years rents >=5% | Export index | + rents + income | 0.056 | 0.191 | 1,252 | 61 | 423 |
| Country-years rents >=5% | Export index | Full + WGI | -0.051 | 0.005 | 672 | 52 | 195 |
| Listed-country sample | TFP growth | + rents + income | 0.135 | 0.751 | 2,535 | 54 | 380 |
| Listed-country sample | TFP growth | Full + WGI | 0.128 | 0.865 | 1,076 | 54 | 154 |
| Countries ever rents >=5% | TFP growth | + rents + income | 0.184 | 0.678 | 2,094 | 45 | 380 |
| Countries ever rents >=5% | TFP growth | Full + WGI | 0.215 | 0.782 | 896 | 45 | 154 |
| Countries mean rents >=5% | TFP growth | + rents + income | 0.410 | 0.478 | 1,327 | 29 | 345 |
| Countries mean rents >=5% | TFP growth | Full + WGI | 0.206 | 0.829 | 576 | 29 | 146 |
| Country-years rents >=5% | TFP growth | + rents + income | 0.301 | 0.584 | 1,214 | 45 | 380 |
| Country-years rents >=5% | TFP growth | Full + WGI | -0.106 | 0.931 | 535 | 39 | 154 |
| Listed-country sample | Manufacturing VA share | + rents + income | -0.286 | 0.722 | 2,824 | 72 | 394 |
| Listed-country sample | Manufacturing VA share | Full + WGI | 0.170 | 0.851 | 1,366 | 72 | 202 |
| Countries ever rents >=5% | Manufacturing VA share | + rents + income | -0.329 | 0.691 | 2,273 | 60 | 394 |
| Countries ever rents >=5% | Manufacturing VA share | Full + WGI | 0.195 | 0.826 | 1,126 | 60 | 202 |
| Countries mean rents >=5% | Manufacturing VA share | + rents + income | -0.096 | 0.920 | 1,490 | 41 | 364 |
| Countries mean rents >=5% | Manufacturing VA share | Full + WGI | 0.095 | 0.925 | 759 | 41 | 194 |
| Country-years rents >=5% | Manufacturing VA share | + rents + income | -0.309 | 0.770 | 1,349 | 57 | 394 |
| Country-years rents >=5% | Manufacturing VA share | Full + WGI | 0.211 | 0.886 | 713 | 52 | 202 |

Interpretation: enforcing `rents >= 5%` at the country-year level creates the only strong negative export-index coefficient under full controls, but that result is not mirrored in TFP or manufacturing. Country-level enforcement (`ever` or `mean` resource rich) does not reproduce the strong full-control export signal.

## Lag/Lead Ladder

Treatment is 0/0.5/1 intensity. Controls are `resource_rents` plus `initial_gdp_per_capita` to preserve the long panel. Cells report `coef (p)`.

| Outcome | Lag 30 | Lag 20 | Lag 10 | Lag 5 | Current | Lead 5 | Lead 10 | Lead 20 | Lead 30 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Export index | 0.034 (0.053) | -0.039 (0.138) | -0.015 (0.476) | 0.012 (0.666) | 0.060 (0.080) | 0.082 (0.012) | 0.062 (0.095) | 0.084 (0.050) | 0.024 (0.333) |
| TFP growth | -0.539 (0.390) | 1.161 (0.336) | -1.102 (0.106) | -0.167 (0.821) | 0.135 (0.751) | 1.162 (0.064) | 0.765 (0.390) | 0.086 (0.893) | 0.460 (0.528) |
| Manufacturing VA share | -0.699 (0.272) | 0.630 (0.183) | 0.002 (0.998) | -0.495 (0.454) | -0.286 (0.722) | -1.249 (0.143) | -1.244 (0.208) | -0.732 (0.471) | -0.008 (0.993) |

Interpretation: the export-index result has lead coefficients that are at least as prominent as the current coefficient, which is a warning sign for treatment timing, differential pre-trends, or reverse coding. TFP and manufacturing do not show a coherent lagged deterioration pattern.

## Fast-Pass Recommendation

Do not promote the current result. The next hardened run should wait for:

1. Explicit outcome architecture with a primary export-concentration/diversification measure whose sign is documented.
2. Separate reporting for export concentration, TFP growth, manufacturing VA share, and the public-investment/capital-formation channel.
3. Treatment recoding that distinguishes binary exposure, scored intensity, market-open resource peers, and uncoded observations.
4. A resource-rich sample rule chosen before estimation: country-level resource-rich pool versus country-year rent exposure.
5. Lag/lead/event-time diagnostics in the run artifact, because the current fast-pass lead ladder is not reassuring.
