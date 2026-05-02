# Result card - catch_up_capital_deepening_not_tfp

**Verdict:** supported - Early capital+human-capital share 61.2% >= 60% and later TFP contribution falls from 1.47pp/yr to 0.85pp/yr.

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
| Capital contribution | +2.40%/yr | +1.91%/yr |
| Human-capital contribution | +0.60%/yr | +0.64%/yr |
| TFP contribution | +1.47%/yr | +0.85%/yr |
| Capital + human-capital share | 61.2% | 64.1% |
| TFP share | 29.9% | 21.4% |

## Country Summary

| ISO3 | Start | Early output growth | Early K+HC share | Early TFP | Later TFP |
|---|---:|---:|---:|---:|---:|
| BRA | 1964 | +3.17% | 74.0% | +1.53% | -0.24% |
| CHL | 1974 | +2.79% | 36.4% | +1.89% | +0.56% |
| CHN | 1978 | +3.95% | 86.0% | +0.56% | +0.90% |
| EST | 1992 | +5.83% | 42.8% | +2.81% | +0.70% |
| IDN | 1967 | +4.41% | 62.3% | +0.92% | +1.01% |
| IND | 1991 | +6.23% | 52.5% | +1.40% | +1.94% |
| IRL | 1987 | +5.04% | 21.4% | +2.50% | +0.71% |
| JPN | 1960 | +6.74% | 62.8% | +2.09% | +0.62% |
| KOR | 1962 | +7.24% | 46.9% | +2.16% | +1.64% |
| MEX | 1960 | +2.50% | 86.3% | +0.34% | -0.35% |
| MYS | 1971 | +3.43% | 164.6% | -2.06% | +0.62% |
| POL | 1990 | +4.50% | 45.1% | +1.89% | +1.09% |
| SGP | 1965 | +6.51% | 70.9% | +0.21% | +0.01% |
| THA | 1961 | +6.43% | 48.7% | +3.21% | +1.46% |
| TUR | 1980 | +1.96% | 143.1% | -0.43% | +0.04% |
| TWN | 1960 | +6.85% | 47.2% | +3.36% | +2.08% |

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
