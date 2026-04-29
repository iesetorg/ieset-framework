# Result card — Nordic outcome persistence decomposition v3 (within-country DiD)

**Verdict:** refuted — at least one pre-registered sign is wrong

Pre-registered falsification: β_reform > 0 at p < 0.10 AND β_stagnation < 0 at p < 0.10 AND placebo |t| < 1.65.

## Primary spec — log GDP per capita PPP (TWFE, country + year FE)

| Term | Estimate | SE | 95% CI | p | Sign expected | Sign correct? |
|---|---:|---:|:---:|---:|:---:|:---:|
| reform_post | -0.0020 | 0.0443 | [-0.089, +0.085] | 0.964 | + | ✗ |
| fiscal_dominance_post | -0.0266 | 0.0611 | [-0.147, +0.094] | 0.664 | − | ✓ |

n = 280 country-years, R² within = 0.266

## Pre-trend placebo (fake treatment 5 years earlier, restricted to pre-treatment sample)

reform_placebo |t| = 0.05 — clean

fd_placebo |t| = 0.43 — clean

## Robustness: drop 2020–2021 COVID years

reform_post (drop-COVID): -0.0018 (SE 0.0422, p=0.967)

fiscal_dominance_post (drop-COVID): -0.0210 (SE 0.0624, p=0.737)

## Secondary outcome: unemployment

reform_post: -0.233 (SE 1.269, p=0.854)

fiscal_dominance_post: +3.024 (SE 1.732, p=0.082)

## Event study — reform cohort (relative to t=−1)

| k | estimate | SE | t |
|---:|---:|---:|---:|
| -5 | +0.003 | 0.039 | +0.07 |
| -4 | +0.015 | 0.037 | +0.41 |
| -3 | -0.050 | 0.058 | -0.86 |
| -2 | -0.063 | 0.055 | -1.14 |
| +0 | -0.066 | 0.045 | -1.47 |
| +1 | -0.060 | 0.040 | -1.48 |
| +2 | -0.072 | 0.044 | -1.62 |
| +3 | -0.065 | 0.042 | -1.53 |
| +4 | -0.062 | 0.042 | -1.50 |
| +5 | -0.065 | 0.038 | -1.73 |
| +6 | -0.065 | 0.034 | -1.91 |
| +7 | -0.060 | 0.033 | -1.83 |
| +8 | -0.049 | 0.038 | -1.28 |
| +9 | -0.056 | 0.035 | -1.60 |
| +10 | -0.053 | 0.032 | -1.64 |

## Event study — fiscal-dominance cohort (relative to t=−1)

| k | estimate | SE | t |
|---:|---:|---:|---:|
| -5 | +0.095 | 0.031 | +3.07 |
| -4 | +0.092 | 0.030 | +3.09 |
| -3 | +0.143 | 0.042 | +3.43 |
| -2 | +0.138 | 0.039 | +3.58 |
| +0 | +0.138 | 0.023 | +5.95 |
| +1 | +0.149 | 0.018 | +8.21 |
| +2 | +0.180 | 0.025 | +7.31 |
| +3 | +0.186 | 0.032 | +5.85 |
| +4 | +0.174 | 0.032 | +5.51 |
| +5 | +0.178 | 0.050 | +3.54 |
| +6 | +0.171 | 0.060 | +2.88 |
| +7 | +0.163 | 0.065 | +2.50 |
| +8 | +0.155 | 0.073 | +2.12 |
| +9 | +0.110 | 0.053 | +2.08 |
| +10 | +0.051 | 0.019 | +2.68 |

## Interpretation

The v3 design did not cleanly confirm the pre-registered pattern. The steelman's concerns about staggered TWFE bias, small n treated cohorts, and pre-trend testability are live. v3.1 should run Callaway-Sant'Anna to handle heterogeneous-effects bias, split Greece into pre- and post-Troika movements, and run synthetic control per treated country for case-level verification before drawing strong conclusions. Honest report below as pre-committed in DISCLOSURE.md.

## Steelman-live concerns

1. **Staggered TWFE with heterogeneous effects**: Goodman-Bacon (2021) bias unaddressed; v3.1 must run Callaway-Sant'Anna.
2. **n=4 treated countries**: pre-trend placebo is low-powered. Clean placebo ≠ parallel trends holds.
3. **Greek 2001-2023 indicator conflates fiscal-dominance 2001-2010 with Troika-austerity 2010+**: v3.2 should split.
4. **Italian GDP decline partly demographic**: working-age-population-adjusted spec in v3.3.

## Provenance

Reproduces deterministically from vintages in `manifest.yaml`. Spec pre-registration in `hypotheses/institutional_quality/nordic_outcome_persistence_decomposition_v3.yaml` with git timestamp predating this run.
