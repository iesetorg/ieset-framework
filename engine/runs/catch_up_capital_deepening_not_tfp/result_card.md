# Result card - catch_up_capital_deepening_not_tfp

**Verdict:** supported - Early capital+human-capital share 65.0% >= 60% and later TFP contribution falls from 1.28pp/yr to 0.57pp/yr.

## Design

PWT panel 1960-2019. For each pre-specified catch-up episode,
5-year annualized output-per-worker growth is decomposed into capital deepening,
human capital, and TFP contributions. The first 15 available episode
years are compared with later episode years.

## Threshold

SUPPORTED if capital + human-capital channels explain at least
60% of positive early catch-up growth and the later TFP
contribution is below the early TFP contribution. REFUTED if early TFP explains
at least 50% and later TFP contribution does not fall. Otherwise PARTIAL.

## Aggregate Metrics

| Metric | Early window | Later window |
|---|---:|---:|
| Observations | 241 | 359 |
| Countries | 17 | 16 |
| Output-per-worker growth | +4.90%/yr | +3.97%/yr |
| Capital contribution | +2.59%/yr | +2.19%/yr |
| Human-capital contribution | +0.60%/yr | +0.64%/yr |
| TFP contribution | +1.28%/yr | +0.57%/yr |
| Capital + human-capital share | 65.0% | 71.2% |
| TFP share | 26.1% | 14.3% |

## Country Summary

| ISO3 | Start | Early output growth | Early K+HC share | Early TFP | Later TFP |
|---|---:|---:|---:|---:|---:|
| BRA | 1964 | +3.17% | 77.3% | +1.43% | -0.41% |
| CHL | 1974 | +2.79% | 39.5% | +1.80% | +0.41% |
| CHN | 1978 | +3.95% | 90.5% | +0.38% | +0.66% |
| EST | 1992 | +5.83% | 46.9% | +2.57% | +0.54% |
| IDN | 1967 | +4.41% | 67.9% | +0.68% | +0.86% |
| IND | 1991 | +6.23% | 56.3% | +1.16% | +1.78% |
| IRL | 1987 | +5.04% | 25.8% | +2.28% | +0.54% |
| JPN | 1960 | +6.74% | 62.3% | +2.12% | +0.46% |
| KOR | 1962 | +7.24% | 47.6% | +2.11% | +1.44% |
| MEX | 1960 | +2.50% | 92.4% | +0.19% | -0.51% |
| MYS | 1971 | +3.43% | 174.1% | -2.39% | -0.04% |
| POL | 1990 | +4.50% | 52.3% | +1.57% | +0.80% |
| SGP | 1965 | +6.51% | 76.8% | -0.18% | -0.34% |
| THA | 1961 | +6.43% | 50.3% | +3.11% | +0.98% |
| TUR | 1980 | +1.96% | 158.7% | -0.73% | -0.34% |
| TWN | 1960 | +6.85% | 48.3% | +3.28% | +1.76% |

## Limitations

- Episode starts are coarse historical markers, not machine-coded treatment dates.
- PWT TFP is only available for years with the full national accounts inputs.
- Negative-growth windows are excluded from the share calculation to avoid unstable
  contribution shares; diagnostics retain observation counts.
- This is a growth-accounting decomposition, not a causal estimate of industrial
  policy.

## Next Robustness Checks

- Re-run with 10-year windows.
- Use all below-40%-of-US catch-up observations, not only named episodes.
- Add WGI/Fraser/Heritage market-institution splits once those datasets are loaded.
