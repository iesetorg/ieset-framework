# Result card - yield_curve_inversion_unemployment_us_1976_2026

**Verdict:** supported - 7 of 9 completed episodes pass; median increase 1.60pp

## Episode Test

Support threshold: at least 70% of completed inversion episodes pass the +0.75pp unemployment follow-through test and median increase >= 1.0pp.

| Start | End | Baseline unemployment | Max unemployment within 24m | Increase pp | Pass |
|---|---:|---:|---:|---:|:---:|
| 1978-09-01 | 1980-04-01 | 6.0 | 7.8 | 1.8 | yes |
| 1980-09-01 | 1981-10-01 | 7.5 | 10.1 | 2.6 | yes |
| 1982-02-01 | 1982-06-01 | 8.9 | 10.8 | 1.9 | yes |
| 1989-01-01 | 1989-06-01 | 5.4 | 6.4 | 1.0 | yes |
| 1989-08-01 | 1989-09-01 | 5.2 | 6.9 | 1.7 | yes |
| 2000-02-01 | 2000-12-01 | 4.1 | 5.7 | 1.6 | yes |
| 2006-02-01 | 2006-03-01 | 4.8 | 5.0 | 0.2 | no |
| 2006-06-01 | 2007-03-01 | 4.6 | 5.6 | 1.0 | yes |
| 2022-07-01 | 2024-08-01 | 3.5 | 4.2 | 0.7 | no |

## Interpretation

The test is associational: yield-curve inversion is treated as a timing signal, not a causal mechanism. Episodes that start fewer than 24 months before the latest unemployment observation are excluded as censored.
