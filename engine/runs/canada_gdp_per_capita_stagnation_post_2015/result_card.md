# Result card — Canada GDP per capita stagnation post-2015

**Verdict:** SUPPORTED — Canada diverged negatively from donor pool post-2015 (β=-0.033, p=0.005). SC gap negative in 100% of post-2015 years.

## Primary spec (TWFE, log GDP pc PPP, 2000-2023)

| Term | Estimate | SE | 95% CI | p | t |
|---|---:|---:|:---:|---:|---:|
| canada_post_2015 | -0.0331 | 0.0115 | [-0.056, -0.010] | 0.005 | -2.87 |
| (robust 2016 cutoff) canada_post_2016 | -0.0358 | 0.0116 | [-0.059, -0.013] | 0.003 | -3.08 |
| (secondary KD-LCU) canada_post_2015 | -0.0333 | 0.0115 | [-0.056, -0.011] | 0.004 | -2.90 |

n = 168 country-years. Donor pool: USA, AUS, NZL, GBR, NOR, CHE.

## Synthetic control

Donor weights: {'USA': 0.2597754683146883, 'AUS': 1.267675173925521e-17, 'NZL': 0.23427900329449677, 'GBR': 0.3144415012020564, 'NOR': 0.0, 'CHE': 0.19150402718875845}
Pre-fit RMSE 2000-2014: 0.0069 log
Post-2015 avg gap (CAN − synthetic): -0.039 log
Fraction of post-2015 years CAN below synthetic: 100%

## Population-growth decomposition (2015 → 2023)

| Group | Δ real GDP (log) | Δ population (log) | Δ GDP per capita (log) |
|---|---:|---:|---:|
| Canada | +0.148 (+16.0%) | +0.116 (+12.3%) | +0.033 (+3.3%) |
| Donor pool (avg) | +0.176 (+19.3%) | +0.052 (+5.3%) | +0.125 (+13.3%) |
| **Gap (CAN − donor)** | **-0.028** | **+0.064** | **-0.092** |

**Decomposition headline:** Of the per-capita gap, 70% attributable to faster Canadian population growth (denominator absorbing output) and 30% attributable to slower real-GDP numerator growth.

## Interpretation

Canadian GDP per capita (PPP) trajectory under the 2015-present policy mix is the question. The TWFE coefficient identifies the deviation from the donor-pool time-average; the synthetic-control coefficient is robustness; the population-growth decomposition is the falsification guard pre-registered in the YAML.

## Steelman concerns

1. Donor pool excludes EU energy-shock countries by design; alternative pool would change β.
2. 2015 cutoff captures Trudeau era + global productivity slowdown + commodity-price cycle.
3. Per-capita gap mechanically reflects rapid Canadian immigration absorbing output.
4. Real-GDP numerator stagnation is the policy-relevant narrower claim and may differ from per-capita.

## Provenance

Reproduces from vintages in `manifest.yaml`. See `replication.py`.
