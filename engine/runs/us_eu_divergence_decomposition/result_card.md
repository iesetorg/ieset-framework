# Result card — US-EU divergence decomposition

**Verdict:** partial — gap widened +0.044 log-points but less than 0.10 threshold

## Descriptive: US vs EU-9 population-weighted log GDP per capita PPP

- 2000 log-gap: +0.251 (US ~+29% higher than EU avg)
- 2023 log-gap: +0.295 (US ~+34% higher than EU avg)
- **Cumulative widening 2000→2023: +0.044 log-points** (~+5% additional widening)

## Nested-phase decomposition (TWFE, donor dummies + time FE)

| Term | β | SE | 95% CI | p | t |
|---|---:|---:|:---:|---:|---:|
| is_usa (baseline level) | +2.2869 | 2.4576 | [-2.556, +7.130] | 0.353 | +0.93 |
| usa_post_2010 (shale era) | +0.0429 | 0.0271 | [-0.010, +0.096] | 0.114 | +1.59 |
| usa_post_2018 (GDPR-era digital reg) | +0.0441 | 0.0134 | [+0.018, +0.071] | 0.001 | +3.29 |
| usa_post_2021 (EU energy crisis) | +0.0729 | 0.0211 | [+0.031, +0.115] | 0.001 | +3.45 |

n = 264 country-years.

## Interpretation

Cumulative widening is +0.044 log-points (below the 0.10 pre-registered threshold). Descriptive direction confirms widening. Post-2010 coefficient is positive.

## Steelman-live concerns

1. PPP GDP per capita understates the dollar-market-rate gap but is more economically meaningful for comparisons.
2. Cross-period interaction coefficients are additive, not isolated — full decomposition of the widening into causal channels would need instrumented or synthetic-control design per phase.
3. EU average masks intra-EU variation: IRL, POL, SWE kept pace with USA; ITA, ESP, DEU diverged more. Country-level dummies would show this.
4. Demographic differences (US pop grew ~15%; EU ~5%) matter for total-GDP comparisons more than per-capita, but per-capita controls for most of this.
5. US measurement advantages on digital-sector output could inflate measured GDP; EU digital-sector mismeasurement could depress it. Size of effect contested in literature.

## Provenance

Reproduces from vintages in `manifest.yaml`. See `replication.py`.
