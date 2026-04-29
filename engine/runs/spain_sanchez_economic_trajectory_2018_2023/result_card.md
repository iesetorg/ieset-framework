# Result card — Spain Sánchez economic trajectory 2018-2023

**Verdict:** PARTIAL — pattern does not cleanly match either uniform direction. output β = -0.003 p=0.906; housing-affordability β = -0.139 p=0.082.

## Multi-outcome TWFE (definition-controlled sub-analyses)

Each outcome reports β_spain_post_2018 separately to test the pre-registered
DIFFERENTIATED pattern (non-negative on output, negative on housing-affordability).

| Outcome | β | SE | 95% CI | p | t | n |
|---|---:|---:|:---:|---:|---:|---:|
| log GDP pc PPP (output — expect ≥0) | -0.0030 | 0.0249 | [-0.052, +0.046] | 0.906 | -0.12 | 152 |
| unemployment rate (lower=better) | -3.3736 | 1.2849 | [-5.924, -0.823] | 0.010 | -2.63 | 124 |
| log house-price index (raw) | -0.1644 | 0.0879 | [-0.339, +0.010] | 0.064 | -1.87 | 124 |
| log HPI / log GDP pc (affordability — expect >0 = worse) | -0.1386 | 0.0788 | [-0.295, +0.018] | 0.082 | -1.76 | 124 |

Donor pool: FRA, ITA, PRT, GRC, DEU, NLD, BEL. IRL excluded from baseline (FDI distortion).

## Missing v1 outcomes (data-gated)

- employment_rate_15_64 — Eurostat lfsi_emp_a not in local vintages
- real_wage_index — OECD DF_EARN not in local vintages
- OECD analytical real house-price-to-income — URN unverified, not in vintages

Substituted: log(Eurostat HPI) / log(WDI GDP pc PPP) as a housing-affordability
proxy. The proxy is upper-bound conservative because it uses national-average
GDP per capita rather than household disposable income (which grew slower in
Spain than GDP per capita).

## Steelman concerns

1. Donor pool is euro-area-only by design; pure monetary-regime confound absorbed.
2. 2018 cutoff covers Sánchez but year FE absorb COVID + energy + ECB shocks common to euro-area.
3. Housing-affordability mechanism may be Spain-supply-constraint (tourism, short-let, Madrid-Barcelona concentration) rather than Sánchez-policy-content.
4. The HPI/GDPpc proxy is a coarser measure than OECD's real-house-price-to-income; sign should be informative even if magnitude is biased.

## Provenance

Reproduces from vintages in `manifest.yaml`. See `replication.py`.
